# Write your API serialisers here.
from rest_framework import serializers, viewsets

from .models import Album, Song, Playlist, DottifyUser

class SongSerializer(serializers.ModelSerializer):
    class Meta:
        model = Song
        fields = ['id', 'title', 'length', 'album'
            ]
        read_only_fields = ['id']

class AlbumSerializer(serializers.ModelSerializer):
    song_set = serializers.SlugRelatedField(
        many=True,
        read_only=True,
        slug_field='title'
        
    )
    class Meta:
        model = Album
        fields = [
            'id',
            'title',
            'artist_name',
            'format',
            'cover_image',
            'retail_price',
            'release_date',
            'slug',
            'song_set'
        ]
        read_only_fields = ['id', 'slug']
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data.pop('artist_account', None)
        return data

class PlaylistSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.display_name', read_only= True)
    songs = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        view_name='song-detail')
    class Meta:
        model = Playlist
        fields = ['id', 'name', 'owner', 'songs', 'created_at'
        ]
        read_only_fields = ['id', 'owner', 'songs']