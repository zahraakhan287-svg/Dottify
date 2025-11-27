import os
import csv
import django
from datetime import datetime

# --- Setup Django ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MusicDBInc.settings')
django.setup()

from dottify.models import Album, Song, DottifyUser
def parse_date(date_str):
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None

def parse_price(price_str):
    try:
        return float(price_str)
    except (ValueError, TypeError):
        return 0.0
# --- Import albums ---
with open('sample_data/albums.csv', newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        album, created = Album.objects.get_or_create(
            title=row['Album'],
            artist_name=row['Artist'],
            release_date=parse_date(row['Released']),
            retail_price=parse_price(row['Price']),
            format=(row.get('Format') or '').strip()
        )

        cover_image = (row.get('CoverImage') or '').strip()
        if cover_image:
            album.cover_image = cover_image
            album.save()

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

