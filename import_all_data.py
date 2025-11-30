import os
import csv
from django.core.files import File
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MusicDBInc.settings')
django.setup()

from dottify.models import Album, Song, DottifyUser
ALBUM_CSV = 'sample_data/albums.csv'
SONG_CSV = 'sample_data/songs.csv'
IMAGES_DIR = 'sample_data/images'
DEFAULT_COVER = 'media/no_cover.jpg'

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

with open(ALBUM_CSV, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        album, created = Album.objects.get_or_create(
            title=row['Album'],
            artist_name=row['Artist'],
            release_date=parse_date(row['Released']),
            retail_price=parse_price(row['Price']),
            format=(row.get('Format') or '').strip()
        )

        cover_image_name = (row.get('CoverImage') or '').strip()
        if cover_image_name:
            cover_image_path = os.path.join(IMAGES_DIR, cover_image_name)
            if os.path.exists(cover_image_path):
                with open(cover_image_path, 'rb') as img_file:
                    album.cover_image.save(os.path.basename(cover_image_path), File(img_file), save=True)
            else:
                with open(DEFAULT_COVER, 'rb') as img_file:
                    album.cover_image.save('no_cover.jpg', File(img_file), save=True)
        else:
            with open(DEFAULT_COVER, 'rb') as img_file:
                album.cover_image.save('no_cover.jpg', File(img_file), save=True)

        print(f"{'Created' if created else 'Exists'} album: {album.title}")

with open(SONG_CSV, newline='', encoding='utf-8') as f:
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

