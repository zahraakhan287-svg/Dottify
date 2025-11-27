from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from .models import Album, Song, Playlist, DottifyUser
from datetime import date, timedelta

class APIRouteTests(APITestCase):

    def setUp(self):
        # Create a DottifyUser
        u = User.objects.create_user(username='annie', email='annie@example.com', password='pw123')
        d_user = DottifyUser.objects.create(user=u, display_name='AnnieMusicLover92')
        self.user_id = d_user.id

        # Create Album
        self.album = Album.objects.create(
            title='Greatest Hits',
            format='SNGL',
            artist_name='Johnny Singer',
            release_date=date.today(),
            retail_price=2.99
        )
        self.album_id = self.album.id

        # Create Songs
        self.song1 = Song.objects.create(title='One Hit Wonder', length=281, album=self.album)
        self.song2 = Song.objects.create(title='Another Bop', length=540, album=self.album)
        self.song1_id = self.song1.id
        self.song2_id = self.song2.id

        # Create Playlist (Public)
        self.playlist = Playlist.objects.create(
            name='Work Jams 2',
            owner=d_user,
            visibility=2
        )
        self.playlist.songs.set([self.song1, self.song2])
        self.playlist_id = self.playlist.id

    def tearDown(self):
        Playlist.objects.all().delete()
        Song.objects.all().delete()
        Album.objects.all().delete()
        DottifyUser.objects.all().delete()
        User.objects.all().delete()

    # ---- Album API tests ----
    def test_album_list(self):
        response = self.client.get('/api/albums/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(album['title'] == 'Greatest Hits' for album in response.json()))

    def test_album_detail(self):
        response = self.client.get(f'/api/albums/{self.album_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'Greatest Hits')

    # ---- Song API tests ----
    def test_song_list(self):
        response = self.client.get('/api/songs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(song['title'] == 'One Hit Wonder' for song in response.json()))

    def test_song_detail(self):
        response = self.client.get(f'/api/songs/{self.song1_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'One Hit Wonder')

    # ---- Playlist API tests ----
    def test_playlist_list_only_public(self):
        response = self.client.get('/api/playlists/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(all(pl['owner'] == 'AnnieMusicLover92' for pl in response.json()))
        self.assertTrue(any(pl['name'] == 'Work Jams 2' for pl in response.json()))

    def test_playlist_detail_only_public(self):
        response = self.client.get(f'/api/playlists/{self.playlist_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['owner'], 'AnnieMusicLover92')
        self.assertEqual(response.json()['name'], 'Work Jams 2')

    # ---- Nested Album-Song API tests ----
    def test_album_song_list(self):
        response = self.client.get(f'/api/albums/{self.album_id}/songs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(any(song['title'] == 'One Hit Wonder' for song in response.json()))

    def test_album_song_detail(self):
        response = self.client.get(f'/api/albums/{self.album_id}/songs/{self.song1_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.json()['title'], 'One Hit Wonder')

    # ---- Statistics API test ----
    def test_statistics(self):
        response = self.client.get('/api/statistics/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertIn('user_count', data)
        self.assertIn('album_count', data)
        self.assertIn('playlist_count', data)
        self.assertIn('song_length_average', data)
