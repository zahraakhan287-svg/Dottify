from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Album, Playlist, Song, DottifyUser
from .forms import AlbumForm, SongForm
from django.utils.text import slugify
# Create your views here.


class HomePageView(ListView): 
    template_name = 'dottify/home.html'
    context_object_name = 'albums'
    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated:
            if user.groups.filter(name='DottifyAdmin').exists():
                return Album.objects.all()
            elif user.groups.filter(name='Artist').exists():
                return Album.objects.filter(artist_account=user)
            else:
                return Album.objects.none()
        else:
            return Album.objects.filter(public=True)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        if user.is_authenticated and user.groups.filter(name='DottifyAdmin').exists():
            context['playlists'] = Playlist.objects.all()
            context['songs'] = Song.objects.all()
        elif user.is_authenticated:
            context['playlists'] = Playlist.objects.filter(owner=user)
        else:
            context['playlists'] = Playlist.objects.filter(visibility=2)  # public playlists
        
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
                return Album.objects.filter(artist_account=user)
        return Album.objects.filter(public=True)
class AlbumSearchView(LoginRequiredMixin, ListView):
    template_name = 'dottify/album_search.html'
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
        slug = kwargs.get('slug')
        if slug != album.slug:
            return redirect('album_detail', pk=album.pk, slug=album.slug)
        return super().get(request, *args, **kwargs)

class AlbumCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Album
    fields = ['title', 'description', 'cover_image']
    template_name = 'albums/album_form.html'

    def test_func(self):
        user = self.request.user
        return user.groups.filter(name__in=['Artist', 'DottifyAdmin']).exists()
    def form_valid(self, form):
        form.instance.artist_account = self.request.user
        return super().form_valid(form)

class AlbumUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Album
    form_class = AlbumForm
    template_name = 'dottify/album_form.html'

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or album.artist_account == user

class AlbumDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Album
    template_name = 'dottify/album_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        album = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or album.artist_account == user

    def handle_no_permission(self):
        return HttpResponseForbidden("You are not allowed to delete this album.")

class SongDetailView(DetailView):
    model = Song
    template_name = 'dottify/song_detail.html'
    context_object_name = 'song'

class SongCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Song
    form_class = SongForm
    template_name = 'dottify/song_form.html'
    
    def test_func(self):
        album_id = self.request.POST.get('album') or self.request.GET.get('album')
        album = get_object_or_404(Album, id=album_id) if album_id else None
        user = self.request.user
        return (user.groups.filter(name='DottifyAdmin').exists() or
                (album and album.artist_account == user))

    def form_valid(self, form):
        return super().form_valid(form)
    
class SongUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
        model = Song
        form_class = SongForm
        template_name = 'dottify/song_form.html'
        def test_func(self):
            song = self.get_object()
            user = self.request.user
            return user.groups.filter(name='DottifyAdmin').exists() or song.album.artist_account == user

        def handle_no_permission(self):
            return HttpResponseForbidden("You are not allowed to edit this song.")
class SongDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Song
    template_name = 'dottify/song_confirm_delete.html'
    success_url = reverse_lazy('home')

    def test_func(self):
        song = self.get_object()
        user = self.request.user
        return user.groups.filter(name='DottifyAdmin').exists() or song.album.artist_account == user

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