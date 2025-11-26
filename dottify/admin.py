from django.contrib import admin
from .models import Album, Song, Playlist, Rating, Comment, DottifyUser

admin.site.register(Album)
admin.site.register(Song)
admin.site.register(Playlist)
admin.site.register(Rating)
admin.site.register(Comment)
admin.site.register(DottifyUser)
