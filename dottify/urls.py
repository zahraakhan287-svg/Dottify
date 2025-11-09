# Write your URL patterns here.
from rest_framework_nested import routers
from django.urls import include, path
from views import AlbumViewSet, PlaylistViewSet, SongViewSet, StatisticAPIView, NestedSongViewSet

router = routers.DefaultRouter()
router.register(r'albums', AlbumViewSet)
router.register(r'playlists', PlaylistViewSet )
router.register(r'songs', SongViewSet)

albums_router = routers.NestedSimpleRouter(router, r'albums', lookup='album')
albums_router.register(r'songs', NestedSongViewSet, basename='album-songs')
urlpatterns = [
    path('', include(router.urls)),
    path('', include(albums_router.urls)),
    path('statistics', StatisticAPIView.as_view())
]
