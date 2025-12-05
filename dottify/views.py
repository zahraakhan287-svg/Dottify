from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Album, Playlist, Song, DottifyUser
from .forms import AlbumForm, SongForm
from django.utils.text import slugify
from django.contrib.auth.models import Group
from .models import DottifyUser
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.db.models import Avg
from django.http import HttpResponse

class RequireLogin401Mixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponse(status=401)
        return super().dispatch(request, *args, **kwargs)


# Create your views here.


class HomePageView(ListView): 
    model = Album
    template_name = "home.html"
    context_object_name = "albums"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        albums = Album.objects.all()

        songs = Song.objects.none()
        playlists = Playlist.objects.filter(visibility=2)

        if user.is_authenticated:

            try:
                dottify_user = DottifyUser.objects.get(user=user)
            except DottifyUser.DoesNotExist:
                dottify_user = None

            if user.groups.filter(name="DottifyAdmin").exists():
                albums = Album.objects.all()
                songs = Song.objects.all()
                playlists = Playlist.objects.all()

            elif user.groups.filter(name="Artist").exists() and dottify_user:
                albums = Album.objects.filter(artist_account=dottify_user)
                songs = Song.objects.filter(album__artist_account=dottify_user)
                playlists = Playlist.objects.filter(owner=dottify_user)

            else:
                albums = Album.objects.filter(public=True)
                songs = Song.objects.none()
                playlists = Playlist.objects.filter(owner=dottify_user)

        playlists = playlists.prefetch_related('songs')

        for album in albums:
            album.can_edit_album = (
                user.is_authenticated and (
                    user.groups.filter(name='DottifyAdmin').exists() or
                    (album.artist_account and album.artist_account.user == user)
                )
            )

        for song in songs:
            song.can_edit_song = (
                user.is_authenticated and (
                    user.groups.filter(name='DottifyAdmin').exists() or
                    (song.album.artist_account and song.album.artist_account.user == user)
                )
            )

        context['albums'] = albums
        context['songs'] = songs
        context['playlists'] = playlists

        return context



    

class AlbumListView(ListView):
    model = Album
    template_name = 'albums/album_list.html'
    context_object_name = 'albums'

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.groups.filter(name= 'DottifyAdmin').exists():
                return Album.objects.all()
            elif user.groups.filter(name='Artist').exists():
                dottify_user = DottifyUser.objects.get(user=user)
                return Album.objects.filter(artist_account=dottify_user)
        return Album.objects.filter(public=True)

class AlbumSearchView(RequireLogin401Mixin, ListView):
    template_name = 'albums/album_search.html'
    context_object_name = 'albums'

    def get_queryset(self):
        user = self.request.user
        query = self.request.GET.get('q', '')

        qs = Album.objects.filter(title__icontains=query)
        if not user.groups.filter(name='DottifyAdmin').exists():
            qs = qs.filter(public=True)

        return qs
class AlbumDetailView(DetailView):
    model = Album
    template_name = 'albums/album_detail.html'
    context_object_name = 'album'

    def get(self, request, *args, **kwargs):
        album = self.get_object()
        url_slug = kwargs.get('slug')

        if url_slug and url_slug != album.slug:
            return redirect('album_detail_slug', pk=album.pk, slug=album.slug)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.get_object()
        user = self.request.user

        artist_account = album.artist_account

        context['songs'] = album.song_set.all()
        context['comments'] = album.comment_set.all()

        context['is_admin'] = (
            user.is_authenticated and 
            user.groups.filter(name='DottifyAdmin').exists()
        )

        context['is_artist'] = (
            user.is_authenticated and
            user.groups.filter(name='Artist').exists() and
            artist_account is not None and
            artist_account.user == user
        )

        context['is_owner'] = (
            user.is_authenticated and
            hasattr(user, 'dottifyuser') and
            artist_account is not None and
            artist_account == user.dottifyuser
        )

        context['can_edit_album'] = (
            user.is_authenticated and (
                user.groups.filter(name='DottifyAdmin').exists() or
                (artist_account is not None and artist_account.user == user)
            )
        )

        return context


class AlbumCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'
    

    def test_func(self):
        user = self.request.user
        return user.groups.filter(name__in=['Artist', 'DottifyAdmin']).exists()
    def form_valid(self, form):
        dottify_user = DottifyUser.objects.get(user=self.request.user)
        form.instance.artist_account = dottify_user
        messages.success(self.request, "Album created successfully!")
        return super().form_valid(form)
    
class AlbumUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return (
            user.groups.filter(name='DottifyAdmin').exists()
            or (album.artist_account and album.artist_account.user == user)
        )

    def form_valid(self, form):
        messages.success(self.request, "Album updated successfully!")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was a problem updating the album.")
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse(
            'album_detail_slug',
            kwargs={'pk': self.object.pk, 'slug': self.object.slug},
        )

class AlbumDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Album
    template_name = 'albums/album_confirm_delete.html'
    success_url = reverse_lazy('album_list')

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or (
            album.artist_account and album.artist_account.user == user
        )
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Album deleted successfully.")
        return super().delete(request, *args, **kwargs)
    
    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to delete this album.")

class SongDetailView(DetailView):
    model = Song
    template_name = 'songs/song_detail.html'
    context_object_name = 'song'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        song = self.get_object()
        artist_account = song.album.artist_account if song.album else None
        all_time_avg = song.rating_set.aggregate(avg=Avg('stars'))['avg'] or 0.0

        sixty_days_ago = timezone.now().date() - timedelta(days=60)
        recent_avg = song.rating_set.filter(
            created_at__gte=sixty_days_ago
        ).aggregate(avg=Avg('stars'))['avg'] or 0.0

        context['all_time_avg'] = f"{all_time_avg:.1f}"
        context['recent_avg'] = f"{recent_avg:.1f}"

        context['can_edit_song'] = (
            user.is_authenticated and
            (
                user.groups.filter(name='DottifyAdmin').exists() or
                (artist_account is not None and artist_account.user == user)
            )
        )
        return context
class SongCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = 'songs/song_form.html'
    
    def test_func(self):
        album_id = self.request.POST.get('album') or self.request.GET.get('album')
        album = get_object_or_404(Album, id=album_id) if album_id else None
        user = self.request.user
        return (user.groups.filter(name='DottifyAdmin').exists() or
                (album and album.artist_account.user == user))

    def form_valid(self, form):
        messages.success(self.request, "Song created successfully!")
        return super().form_valid(form)
    def form_invalid(self, form):
        messages.error(self.request, "There was a problem creating the song.")
        return super().form_invalid(form)
    
class SongUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
        model = Song
        form_class = SongForm
        template_name = 'songs/song_form.html'
        def test_func(self):
            song = self.get_object()
            user = self.request.user
            return user.groups.filter(name='DottifyAdmin').exists() or (song.album.artist_account and song.album.artist_account.user == user)
        def form_valid(self, form):
            messages.success(self.request, "Song updated successfully!")
            return super().form_valid(form)

        def form_invalid(self, form):
            messages.error(self.request, "There was a problem updating the song.")
            return super().form_invalid(form)
        def handle_no_permission(self):
            return HttpResponseForbidden("You are not allowed to edit this song.")

class SongDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Song
    template_name = 'songs/song_confirm_delete.html'

    def test_func(self):
        song = self.get_object()
        user = self.request.user
        return (
            user.groups.filter(name='DottifyAdmin').exists() or
            (song.album.artist_account and song.album.artist_account.user == user)
        )

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to delete this song.")
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, "Song deleted successfully.")
        return super().delete(request, *args, **kwargs)
    def get_success_url(self):
        album = self.object.album
        return reverse('album_detail_slug', kwargs={'pk': album.pk, 'slug': album.slug})

class DottifyUserDetailView(DetailView):
    model= DottifyUser
    template_name = 'users/user_detail.html'
    context_object_name= 'dottify_user'
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        slug = kwargs.get('slug')
        correct_slug = slugify(user.display_name)
        if slug != correct_slug:
            return redirect('user_detail_slug', pk=user.pk, slug=correct_slug)
        return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['playlists'] = Playlist.objects.filter(owner=self.object).prefetch_related('songs')
        return context