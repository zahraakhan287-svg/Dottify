from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Group
from .models import Album, Song, Playlist, DottifyUser

class DottifyViewsTestCase(TestCase): 
    def setUp(self):   
        self.artist_group = Group.objects.create(name='Artist')
        self.admin_group = Group.objects.create(name='DottifyAdmin')
        self.artist_user = User.objects.create_user(username='artist', password='password')
        self.artist_user.groups.add(self.artist_group)
        self.admin_user = User.objects.create_user(username='admin', password='password')
        self.admin_user.groups.add(self.admin_group)
        self.regular_user = User.objects.create_user(username='regular', password='password')
        self.dottify_user = DottifyUser.objects.create(user=self.regular_user, display_name='Cool User')
        self.album1 = Album.objects.create(title='Album One', artist_account=self.artist_user, public=True)
        self.song1 = Song.objects.create(title='Song One', album=self.album1)
        self.playlist1 = Playlist.objects.create(title='Playlist One', user=self.regular_user, public=True)
        self.client = Client()

    def test_home_anonymous(self):
        response = self.client.get(reverse('home'))
        self.assertContains(response, self.album1.title)
        self.assertNotContains(response, self.song1.title)

    def test_home_artist_user(self):
        self.client.login(username='artist', password='password')
        response = self.client.get(reverse('home'))
        self.assertContains(response, self.album1.title)
        self.assertNotContains(response, self.playlist1.title)

    def test_home_admin_user(self):
        self.client.login(username='admin', password='password')
        response = self.client.get(reverse('home'))
        self.assertContains(response, self.album1.title)
        self.assertContains(response, self.song1.title)
        self.assertContains(response, self.playlist1.title)

    def test_album_search_logged_in(self):
        self.client.login(username='regular', password='password')
        response = self.client.get(reverse('album_search') + '?q=Album')
        self.assertContains(response, self.album1.title)

    def test_album_search_anonymous_redirect(self):
        response = self.client.get(reverse('album_search') + '?q=Album')
        self.assertEqual(response.status_code, 302)  # Redirect to login

    def test_album_create_artist_allowed(self):
        self.client.login(username='artist', password='password')
        response = self.client.post(reverse('album_create'), {'title': 'New Album'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Album.objects.filter(title='New Album').exists())

    def test_album_create_regular_forbidden(self):
        self.client.login(username='regular', password='password')
        response = self.client.get(reverse('album_create'))
        self.assertEqual(response.status_code, 403)

    def test_album_update_artist_allowed(self):
        self.client.login(username='artist', password='password')
        response = self.client.post(reverse('album_update', args=[self.album1.pk]), {'title': 'Updated Album'})
        self.assertEqual(response.status_code, 302)
        self.album1.refresh_from_db()
        self.assertEqual(self.album1.title, 'Updated Album')

    def test_album_delete_admin_allowed(self):
        self.client.login(username='admin', password='password')
        response = self.client.post(reverse('album_delete', args=[self.album1.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Album.objects.filter(pk=self.album1.pk).exists())

    def test_song_create_artist_allowed(self):
        self.client.login(username='artist', password='password')
        response = self.client.post(reverse('song_create'), {'title': 'New Song', 'album': self.album1.pk})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Song.objects.filter(title='New Song').exists())

    def test_song_update_artist_allowed(self):
        self.client.login(username='artist', password='password')
        response = self.client.post(reverse('song_update', args=[self.song1.pk]), {'title': 'Updated Song', 'album': self.album1.pk})
        self.assertEqual(response.status_code, 302)
        self.song1.refresh_from_db()
        self.assertEqual(self.song1.title, 'Updated Song')

    def test_dottify_user_slug_redirect(self):
        response = self.client.get(reverse('user_detail', args=[self.dottify_user.pk, 'wrong-slug']))
        self.assertRedirects(response, reverse('user_detail', args=[self.dottify_user.pk, self.dottify_user.slug]))