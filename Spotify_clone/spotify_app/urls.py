from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search, name='search'),
    path('genre/<slug:slug>/', views.genre_detail, name='genre_detail'),
    path('album/<int:album_id>/', views.album_detail, name='album_detail'),
    path('artist/<int:artist_id>/', views.artist_detail, name='artist_detail'),
    path('playlist/<int:playlist_id>/', views.playlist_detail, name='playlist_detail'),
    path('playlist/create/', views.create_playlist, name='create_playlist'),
    path('playlist/<int:playlist_id>/add/<int:song_id>/', views.playlist_add_song, name='playlist_add_song'),
    path('song/<int:song_id>/add-to-playlist/', views.add_to_playlist, name='add_to_playlist'),
    path('playlist/<int:playlist_id>/remove/<int:song_id>/', views.playlist_remove_song, name='playlist_remove_song'),
    path('playlist/<int:playlist_id>/delete/', views.playlist_delete, name='playlist_delete'),
    path('library/', views.library, name='library'),
    path('collection/tracks/', views.liked_songs, name='liked_songs'),
    path('song/<int:song_id>/like/', views.toggle_like, name='toggle_like'),
    path('login/', views.user_login, name='login'),
    path('signup/', views.user_signup, name='signup'),
    path('logout/', views.user_logout, name='logout'),
    path('demo-login/', views.demo_login, name='demo_login'),
]
