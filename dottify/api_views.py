# Use this file for your API viewsets only
# E.g., from rest_framework import ...
from rest_framework import serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
#from rest_framework_nested import routers
from django.contrib.auth import get_user_model
from django.db.models import Avg

from .models import Album, Song, Playlist, DottifyUser

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ['id', 'title', 'album', 'length']

class AlbumSerializer(serializers.ModelSerializer):
    songset = serializers.SlugRelatedField(many= True, read_only= True, slug_field= 'title')
    class Meta:
        model = Album
        exclude = ['artist_account']

class PlaylistSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.display_name'), read_only= True
    songs = serializers.HyperlinkedRelatedField(many=True, read_only=True,view_name='song-detail')
    class Meta:
        model = Playlist
        fields = ['id', 'title', 'owner', 'songs', 'is_public'
        ]

#ViewSets 
class AlbumViewSet(viewsets.ModelViewSet):
    serializer_class = AlbumSerializer
    queryset = Album.objects.all()
    

class SongViewSet(viewsets.ModelViewSet): 
    queryset = Song.objects.all()
    serializer_class = SongSerializer


class PlaylistViewSet(viewsets.ModelViewSet):
    queryset = Playlist.objects.filter(is_public= True)
    serializer_class = PlaylistSerializer


class NestedSongViewSet(viewsets.ModelViewSet):
    serializer_class = SongSerializer

    def get_queryset(self):
        album_id = self.kwargs['album']  
        return Song.objects.filter(album_id=album_id)
        
class StatisticsAPIView(viewsets.ModelViewSet):
    def get(self, kwargs): 
        data = {
            'user_count': DottifyUser.objects.count(),
            'album_count': Album.objects.count(),
            'playlist_count': Playlist.objects.count(),
            'song_length_average': Song.objects.aggregate(Avg('duration'))['duration_avg'] or 0,
            
        }
        return Response(data)