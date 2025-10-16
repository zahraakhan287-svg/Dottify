from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User

def increments_validator(value):
    '''
    Makes sure values increment in 0.5's
    '''
    if value * 2 % 1 != 0 :
        raise ValidationError("Stars should increment in 0.5's")
    
def valid_release_date(value):
    '''
    This makes sure that the release date is not more than six months away.
    '''
    rn = timezone.now().date()
    add_six_month = rn + timedelta(days=183)
    if value > add_six_month:
        raise ValidationError("Release date must be under 6 months")
    
# Create your models here.
class Album(models.Model):
    FORMAT_CHOICES = [
        ('SNGL', 'Single'),
        ('RMST', 'Remaster'),
        ('DLUX', 'Deluxe'),
        ('COMP', 'Compilation'),
        ('LIVE', 'Live Recording'),
    ]
    title = models.CharField(max_length=800,null=False, blank= False)
    cover_image = models.ImageField(blank= True, null=True, default='default_cover.jpg')
    artist_name = models.CharField(max_length=800, null=False, blank= False)
    format = models.CharField(choices=FORMAT_CHOICES, max_length=4, blank=True, null= True)
    artist_account = models.ForeignKey('DottifyUser', on_delete=models.SET_NULL, null=True, blank=True)    
    retail_price = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.00), MaxValueValidator(999.99)])
    release_date = models.DateField(validators=[valid_release_date])
    slug = models.SlugField(blank=True, editable=False)

    class Meta: 
        constraints = [
            models.UniqueConstraint(
                fields= ['title', 'artist_name', 'format'],
                name= 'unique_album_per_artist_and_format'
            )
        ]
    
    def save(self, *args, **kwargs):
        self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} by {self.artist_name} ({self.format or 'Standard'})"
    
class Song(models.Model):
    title = models.CharField(max_length=800, null= False, blank= False)
    length = models.PositiveIntegerField(validators=[MinValueValidator(10)])
    position = models.PositiveIntegerField(null= True, blank= True, editable=False)
    album = models.ForeignKey('Album', on_delete = models.CASCADE, null= False, blank= False)
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['album', 'title'],
                name='unique_song_title_per_album'
            )
        ]
        ordering = ['position']
    def save(self, *args, **kwargs):
        if self.position is None:
            last_song = Song.objects.filter(album=self.album).order_by('-position').first()
            self.position = 1 if not last_song else last_song.position + 1
        super().save(*args, **kwargs)

    def __str__(self):
        mins, secs = divmod(self.length, 60)
        return f"{self.title} ({mins}:{secs:02d})"

class Playlist(models.Model):
    VISIBILITY_CHOICES = [
        (0, 'Hidden'),
        (1, 'Unlisted'),
        (2, 'Public'),
    ]
    name = models.CharField(max_length=800)
    created_at = models.DateTimeField(auto_now_add=True)
    songs = models.ManyToManyField('Song')
    visibility = models.IntegerField(choices=VISIBILITY_CHOICES, default=0)
    owner = models.ForeignKey('DottifyUser', on_delete=models.CASCADE )


    def __str__(self):
        return f"{self.name} ({self.get_visibility_display()})"

class DottifyUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    display_name = models.CharField(max_length=800, null= False, blank= False)

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
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null= True, blank=True)
    
    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(stars__gte=0.0) & models.Q(stars__lte=5.0),
                name='rating_stars_between_0_and_5'
            )
        ]


    def __str__(self):
        if self.song:
            target = f"song '{self.song.title}'"
        elif self.album:
            target = f"album '{self.album.title}'"
        else:
            target = "unknown item"
        return f"{self.user.display_name} rated {target} {self.stars}★"

class Comment(models.Model):
    comment_text = models.TextField()
    user = models.ForeignKey('DottifyUser', on_delete=models.CASCADE)
    song = models.ForeignKey('Song', on_delete=models.CASCADE, null=True, blank=True)
    album = models.ForeignKey('Album', on_delete=models.CASCADE, null= True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        target = self.song or self.album
        return f"{self.user.display_name} on {target}: {self.comment_text[:40]}..."