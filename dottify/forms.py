# Any form helpers should go in this file.
from django import forms
from .models import Album, Song

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'description', 'cover_image']

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'album', 'length']