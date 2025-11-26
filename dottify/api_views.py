# Use this file for your API viewsets only
# E.g., from rest_framework import ...
from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Avg

from .models import Album, Song, Playlist, DottifyUser
from .serializers import AlbumSerializer, SongSerializer, PlaylistSerializer



 
class AlbumViewSet(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer
    queryset = Album.objects.all()
    

class SongViewSet(viewsets.ModelViewSet): 
    queryset = Song.objects.all()
    serializer_class = SongSerializer


class PlaylistViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Playlist.objects.filter(visibility=2)
    serializer_class = PlaylistSerializer


class NestedSongViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SongSerializer

    def get_queryset(self):
        album_id = self.kwargs.get('album_pk')
        return Song.objects.filter(album_id=album_id)
        
class StatisticsAPIView(APIView):
    def get(self,request, *args, **kwargs): 
        data = {
            'user_count': DottifyUser.objects.count(),
            'album_count': Album.objects.count(),
            'playlist_count': Playlist.objects.count(),
            'song_length_average': Song.objects.aggregate(Avg('length'))['length__avg'] or 0,
            
        }
        return Response(data)