from django.db import models
from django.contrib.auth.models import User

class Genre(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    color = models.CharField(max_length=20, default="#1E3264", help_text="Hex code or gradient for card")
    image_url = models.CharField(max_length=500, blank=True, default="")

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Artist(models.Model):
    name = models.CharField(max_length=150)
    bio = models.TextField(blank=True, default="")
    image_url = models.CharField(max_length=500, blank=True, default="")
    is_verified = models.BooleanField(default=True)
    monthly_listeners = models.PositiveIntegerField(default=1500000)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def formatted_listeners(self):
        return f"{self.monthly_listeners:,}"

class Album(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='albums')
    cover_image_url = models.CharField(max_length=500, blank=True, default="")
    release_date = models.CharField(max_length=50, blank=True, default="2024")
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='albums')
    is_popular = models.BooleanField(default=False)

    class Meta:
        ordering = ['-release_date', 'title']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"

    @property
    def song_count(self):
        return self.songs.count()

class Song(models.Model):
    title = models.CharField(max_length=200)
    artist = models.ForeignKey(Artist, on_delete=models.CASCADE, related_name='songs')
    album = models.ForeignKey(Album, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    genre = models.ForeignKey(Genre, on_delete=models.SET_NULL, null=True, blank=True, related_name='songs')
    duration_seconds = models.PositiveIntegerField(default=180)
    audio_file = models.FileField(upload_to='songs/', blank=True, null=True)
    audio_url = models.CharField(max_length=500, blank=True, null=True)
    cover_image_url = models.CharField(max_length=500, blank=True, null=True)
    plays_count = models.PositiveIntegerField(default=0)
    is_trending = models.BooleanField(default=False)
    is_popular = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-plays_count', '-created_at']

    def __str__(self):
        return f"{self.title} - {self.artist.name}"

    @property
    def formatted_duration(self):
        minutes = self.duration_seconds // 60
        seconds = self.duration_seconds % 60
        return f"{minutes}:{seconds:02d}"

    @property
    def formatted_plays(self):
        return f"{self.plays_count:,}"

    def get_audio_url(self):
        if self.audio_file:
            try:
                return self.audio_file.url
            except Exception:
                pass
        return self.audio_url or ""

    def get_cover_url(self):
        if self.cover_image_url:
            return self.cover_image_url
        if self.album and self.album.cover_image_url:
            return self.album.cover_image_url
        if self.artist and self.artist.image_url:
            return self.artist.image_url
        return "https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?w=300&h=300&fit=crop"

class Playlist(models.Model):
    title = models.CharField(max_length=150)
    description = models.TextField(blank=True, default="")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='playlists')
    cover_image_url = models.CharField(max_length=500, blank=True, default="")
    is_public = models.BooleanField(default=True)
    songs = models.ManyToManyField(Song, blank=True, related_name='playlists')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.username}"

    @property
    def song_count(self):
        return self.songs.count()

    def get_cover_url(self):
        if self.cover_image_url:
            return self.cover_image_url
        first_song = self.songs.first()
        if first_song:
            return first_song.get_cover_url()
        return "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?w=300&h=300&fit=crop"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    song = models.ForeignKey(Song, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'song')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} likes {self.song.title}"
