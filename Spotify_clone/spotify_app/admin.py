from django.contrib import admin
from .models import Genre, Artist, Album, Song, Playlist, Favorite, ArtistFollow, UserProfile

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'color')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'monthly_listeners', 'is_verified', 'follower_count')
    search_fields = ('name',)
    list_filter = ('is_verified',)

    def follower_count(self, obj):
        return obj.followers.count()
    follower_count.short_description = 'Followers'

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'release_date', 'genre', 'is_popular')
    list_filter = ('is_popular', 'genre')
    search_fields = ('title', 'artist__name')

@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = ('title', 'artist', 'album', 'genre', 'duration_seconds', 'plays_count', 'is_trending', 'is_popular')
    list_filter = ('genre', 'is_trending', 'is_popular')
    search_fields = ('title', 'artist__name', 'album__title')

@admin.register(Playlist)
class PlaylistAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_public', 'created_at')
    list_filter = ('is_public',)
    search_fields = ('title', 'user__username')

@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'song', 'created_at')
    search_fields = ('user__username', 'song__title')

@admin.register(ArtistFollow)
class ArtistFollowAdmin(admin.ModelAdmin):
    list_display = ('user', 'artist', 'followed_at')
    search_fields = ('user__username', 'artist__name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_public')
    search_fields = ('user__username',)
    list_filter = ('is_public',)
