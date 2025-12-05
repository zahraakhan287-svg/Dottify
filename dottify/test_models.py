from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from dottify.models import Album, Song, Playlist, DottifyUser

class Setup(TestCase):
    def setUp(self):
        self.user = DottifyUser.objects.create(display_name="Test Artist")
        self.album = Album.objects.create(
            title="Test album",
            artist_name="Test Artist",
            artist_account=self.user,
            retail_price=9.99,
            format="SNGL",
            release_date=timezone.now().date()
        )

class PlaylistModelTesting(Setup):
    def test_playlist(self):
        song = Song.objects.create(
            title="My Song", running_time=120, album=self.album
        )
        playlist = Playlist.objects.create(
            name="My Playlist",
            owner=self.user
        )
        playlist.songs.add(song)
        self.assertEqual(playlist.visibility, 0)
        self.assertIn(song, playlist.songs.all())
        self.assertIsNotNone(playlist.created_at)

class DottifyUserTest(TestCase):
    def test_displayname_required(self):
        with self.assertRaises(ValidationError):
            DottifyUser.objects.create()
