from django.utils import timezone
from django.db import models
from django.forms import ValidationError
from django.urls import reverse
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator

from django.contrib.auth.models import User
from .validators import increments_validator, valid_release_date

# Create your models here.
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.text import slugify


class Album(models.Model):
    FORMAT_CHOICES = [
        ('SNGL', 'Single'),
        ('RMST', 'Remaster'),
        ('DLUX', 'Deluxe Edition'),
        ('COMP', 'Compilation'),
        ('LIVE', 'Live Recording'),
    ]

    title = models.CharField(max_length=800)
    cover_image = models.ImageField(blank=True, null=True, default='no_cover.jpg')
    artist_name = models.CharField(max_length=800)
    format = models.CharField(choices=FORMAT_CHOICES, max_length=4, blank=True, null=True)
    artist_account = models.ForeignKey('DottifyUser', on_delete=models.SET_NULL,
                                       null=True, blank=True)
    retail_price = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0.00), MaxValueValidator(999.99)],
        default=0.00
    )
    release_date = models.DateField(validators=[valid_release_date],default=timezone.now
    )
    slug = models.SlugField(blank=True, null=True, editable=False)
    public = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['title', 'artist_name', 'format'],
                name='unique_album_per_artist_and_format'
            )
        ]
    def __setattr__(self, name, value):

        if name == "artist_account" and isinstance(value, User):
            dottify_user, created = DottifyUser.objects.get_or_create(
            user=value,
            defaults={"display_name": value.username}
            )
            value = dottify_user

        super().__setattr__(name, value)

    def clean(self):

        if isinstance(self.artist_account, User):
            dottify_user, created = DottifyUser.objects.get_or_create(
                user=self.artist_account,
                defaults={"display_name": self.artist_account.username}
            )
            self.artist_account = dottify_user

    def save(self, *args, **kwargs):
        self.clean()

        base_slug = slugify(self.title) or "album"
        slug = base_slug
        counter = 1
        while Album.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1
        self.slug = slug

        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse(
            'album_detail_slug',
            kwargs={'pk': self.pk, 'slug': self.slug},
        )

    
class Song(models.Model):
    title = models.CharField(max_length=800, null=False, blank=False)
    length = models.PositiveIntegerField(validators=[MinValueValidator(10)], default=10)
    position = models.PositiveIntegerField(null=True, blank=True, editable=False)
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['album', 'title'],
                name='unique_song_title_per_album'
            )
        ]
        ordering = ['position']
    @property
    def running_time(self):
        return self.length

    @running_time.setter
    def running_time(self, value):
        self.length = value

    def save(self, *args, **kwargs):
        if self.position is None:
            last_song = Song.objects.filter(album=self.album).order_by('-position').first()
            self.position = 1 if not last_song else last_song.position + 1
        super().save(*args, **kwargs)

    def __str__(self):
        mins, secs = divmod(self.length, 60)
        return f"{self.title} ({mins}:{secs:02d})"
    def get_absolute_url(self):
        return reverse('song_detail', args=[self.pk])

class Playlist(models.Model):
    VISIBILITY_CHOICES = [
        (0, 'Hidden'),
        (1, 'Unlisted'),
        (2, 'Public'),
    ]
    name = models.CharField(max_length=800)
    created_at = models.DateTimeField(auto_now_add=True)
    songs = models.ManyToManyField('Song', blank= True)
    visibility = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)
    owner = models.ForeignKey('DottifyUser', on_delete=models.CASCADE )


    def __str__(self):
        return f"{self.name} ({self.get_visibility_display()})"

class DottifyUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    display_name = models.CharField(max_length=800, null=False, blank=False)
    from django.core.exceptions import ValidationError

    def clean(self):
        if not self.display_name:
            raise ValidationError("display_name is required")
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.display_name
    
class Rating(models.Model):
    stars = models.DecimalField(max_digits=2, decimal_places=1,validators=[
            MinValueValidator(0.0),
            MaxValueValidator(5.0),
            increments_validator
        ]
    )
    user = models.ForeignKey('DottifyUser', on_delete=models.CASCADE)
    song = models.ForeignKey('Song', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(stars__gte=0.0) & models.Q(stars__lte=5.0),
                name='rating_stars_between_0_and_5'
            )
        ]
    def __str__(self):
        return f"{self.user.display_name} rated '{self.song.title}' {self.stars}★"


class Comment(models.Model):
    comment_text = models.TextField()
    user = models.ForeignKey('DottifyUser', on_delete=models.CASCADE)
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null= True, blank=True)
    song = models.ForeignKey('Song', on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def clean(self): 
        if (self.song and self.album) or (not self.song and not self.album):
            raise ValidationError("Comment only flags exactly one of the two ")
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        target = self.song or self.album
        return f"{self.user.display_name} on {target}: {self.comment_text[:40]}..."