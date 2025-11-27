from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Album, Playlist, Song, DottifyUser
from .forms import AlbumForm, SongForm
from django.utils.text import slugify
from django.contrib.auth.models import Group
from .models import DottifyUser

# Create your views here.


class HomePageView(ListView): 
    template_name = 'home.html'
    context_object_name = 'albums'
    def get_queryset(self):
        return Album.objects.none()  
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user  

        albums = Album.objects.filter(public=True)
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
                playlists = Playlist.objects.filter(owner=dottify_user)
                albums = Album.objects.none()
                songs = Song.objects.none()
        playlists = playlists.prefetch_related('songs')


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

class AlbumSearchView(LoginRequiredMixin, ListView):
    template_name = 'albums/album_search.html'
    context_object_name = 'albums'

    def get_queryset(self):
        query = self.request.GET.get('q', '')
        return Album.objects.filter(title__icontains=query)
    
class AlbumDetailView(DetailView):
    model = Album
    template_name = 'albums/album_detail.html'
    context_object_name = 'album'
    def get(self, request, *args, **kwargs):
        album = self.get_object()
        url_slug = kwargs.get('slug')

        if   url_slug is None or url_slug != album.slug:
            return redirect('album_detail_slug', pk=album.pk, slug=album.slug)
        return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        album = self.get_object()
        user = self.request.user

        artist_account = album.artist_account

        context['songs'] = album.song_set.all()
        context['comments'] = album.comment_set.all()

        context['is_admin'] = user.is_authenticated and user.groups.filter(name='DottifyAdmin').exists()
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
            user.is_authenticated and
            (
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
        return super().form_valid(form)

class AlbumUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'albums/album_form.html'

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or album.artist_account.user == user

class AlbumDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Album
    template_name = 'albums/album_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or album.artist_account.user == user

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to delete this album.")

class SongDetailView(DetailView):
    model = Song
    template_name = 'song_detail.html'
    context_object_name = 'song'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        song = self.get_object()
        artist_account = song.album.artist_account if song.album else None

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
    template_name = 'dottify/song_form.html'
    
    def test_func(self):
        album_id = self.request.POST.get('album') or self.request.GET.get('album')
        album = get_object_or_404(Album, id=album_id) if album_id else None
        user = self.request.user
        return (user.groups.filter(name='DottifyAdmin').exists() or
                (album and album.artist_account.user == user))

    def form_valid(self, form):
        return super().form_valid(form)
    
class SongUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
        model = Song
        form_class = SongForm
        template_name = 'dottify/song_form.html'
        def test_func(self):
            song = self.get_object()
            user = self.request.user
            return user.groups.filter(name='DottifyAdmin').exists() or song.album.artist_account.user == user

        def handle_no_permission(self):
            return HttpResponseForbidden("You are not allowed to edit this song.")
class SongDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Song
    template_name = 'dottify/song_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        song = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or song.album.artist_account.user == user

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to delete this song.")
    
class DottifyUserDetailView(DetailView):
    model= DottifyUser
    template_name = 'dottify/user_detail.html'
    context_object_name= 'dottify_user'
    
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        slug = kwargs.get('slug')
        correct_slug = slugify(user.display_name)
        if slug != correct_slug:
            return redirect('user_detail', pk=user.pk, slug=correct_slug)
        return super().get(request, *args, **kwargs)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['playlists'] = Playlist.objects.filter(owner=self.object).prefetch_related('songs')
        return context