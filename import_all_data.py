import os
import csv
import django
from datetime import datetime

# --- Setup Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MusicDBInc.settings')
django.setup()

from dottify.models import Album, Song, DottifyUser

# --- Import albums ---
with open('sample_data/albums.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        album, created = Album.objects.get_or_create(
            title=row['Album'],
            artist_name=row['Artist'],
            release_date=row['Released'] or None,
            retail_price=row['Price'] or 0,
            format=row['Format'] or '',
        )
        print(f"{'Created' if created else 'Exists'} album: {album.title}")

# --- Import songs ---
with open('sample_data/songs.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        album_id = row['Album']
        try:
            album = Album.objects.get(id=album_id)
        except Album.DoesNotExist:
            print(f"Skipping song {row['Song']} (album {album_id} not found)")
            continue

        song, created = Song.objects.get_or_create(
            title=row['Song'],
            album=album,
            length=row['Duration'] or 0
        )
        print(f"{'Created' if created else 'Exists'} song: {song.title}")

