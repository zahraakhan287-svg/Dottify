# Write your URL patterns here.
from rest_framework_nested import routers
from django.urls import path, include
from .api_views import (
    AlbumViewSet,
    SongViewSet,
    PlaylistViewSet,
    NestedSongViewSet,
    StatisticsAPIView
)
from .views import (
    AlbumListView,
    AlbumDetailView,
    AlbumCreateView,
    AlbumSearchView,
    AlbumUpdateView,
    AlbumDeleteView,
    SongDetailView,
    SongCreateView,
    SongUpdateView,
    SongDeleteView,
    DottifyUserDetailView,
    HomePageView,
)
from django.contrib.auth.views import LogoutView, LoginView


router = routers.DefaultRouter()
router.register(r'albums', AlbumViewSet)
router.register(r'songs', SongViewSet)
router.register(r'playlists', PlaylistViewSet)

albums_router = routers.NestedDefaultRouter(router, r'albums', lookup='album')
albums_router.register(r'songs', NestedSongViewSet, basename='album-songs')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/', include(albums_router.urls)),
    path('api/statistics/', StatisticsAPIView.as_view(), name='statistics'),
    
    path('', HomePageView.as_view(), name='home'),
    
    
    path('albums/', AlbumListView.as_view(), name='album_list'),
    path('albums/search/', AlbumSearchView.as_view(), name='album_search'),
    path('albums/new/', AlbumCreateView.as_view(), name='album_create'),
    path('albums/<int:pk>/<slug:slug>/', AlbumDetailView.as_view(), name='album_detail_slug'),

    path('albums/<int:pk>/', AlbumDetailView.as_view(), name='album_detail'),
    path('albums/<int:pk>/edit/', AlbumUpdateView.as_view(), name='album_update'),
    path('albums/<int:pk>/delete/', AlbumDeleteView.as_view(), name='album_delete'),

    path('songs/<int:pk>/', SongDetailView.as_view(), name='song_detail'),
    path('songs/new/', SongCreateView.as_view(), name='song_create'),
    path('songs/<int:pk>/edit/', SongUpdateView.as_view(), name='song_update'),
    path('songs/<int:pk>/delete/', SongDeleteView.as_view(), name='song_delete'),
    
    path('users/<int:pk>/<slug:slug>/', DottifyUserDetailView.as_view(), name='user_detail_slug'),
    path('users/<int:pk>/', DottifyUserDetailView.as_view(), name='user_detail'),

    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(next_page= 'home'), name='logout'),
    ]