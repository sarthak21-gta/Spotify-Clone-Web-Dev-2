from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('songs/', views.songs, name='songs'),
    path('songs/<int:song_id>/', views.song_detail, name='song_detail'),
    path('playlists/', views.playlists, name='playlists'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
]
