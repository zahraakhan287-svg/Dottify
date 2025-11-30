# Any form helpers should go in this file.
from django import forms
from .models import Album, Song
from crispy_forms.helper import FormHelper

class AlbumForm(forms.ModelForm):
    class Meta:
        model = Album
        fields = ['title', 'cover_image', 'artist_name', 'retail_price', 'release_date', 'format']

class SongForm(forms.ModelForm):
    class Meta:
        model = Song
        fields = ['title', 'album', 'length']