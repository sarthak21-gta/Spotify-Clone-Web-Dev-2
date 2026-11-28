from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Song, Album, Artist, Playlist, Genre, Favorite

def home(request):
    featured_playlists = Playlist.objects.filter(is_public=True)[:6]
    popular_albums = Album.objects.all().order_by('-release_date')[:6]
    popular_artists = Artist.objects.all().order_by('-monthly_listeners')[:6]
    trending_songs = Song.objects.filter(is_trending=True)[:10]
    if not trending_songs:
        trending_songs = Song.objects.all()[:10]
    
    genres = Genre.objects.all()[:6]

    quick_picks = list(popular_albums[:4]) + list(featured_playlists[:2])

    context = {
        'quick_picks': quick_picks,
        'featured_playlists': featured_playlists,
        'popular_albums': popular_albums,
        'popular_artists': popular_artists,
        'trending_songs': trending_songs,
        'genres': genres,
    }
    return render(request, 'home.html', context)

def search(request):
    query = request.GET.get('q', '').strip()
    songs = []
    artists = []
    albums = []
    playlists = []
    top_result = None

    if query:
        songs = Song.objects.filter(
            Q(title__icontains=query) |
            Q(artist__name__icontains=query) |
            Q(album__title__icontains=query)
        ).select_related('artist', 'album')[:10]

        artists = Artist.objects.filter(name__icontains=query)[:5]
        albums = Album.objects.filter(
            Q(title__icontains=query) |
            Q(artist__name__icontains=query)
        ).select_related('artist')[:6]
        playlists = Playlist.objects.filter(title__icontains=query, is_public=True)[:6]

        if artists:
            top_result = {'type': 'artist', 'object': artists[0]}
        elif songs:
            top_result = {'type': 'song', 'object': songs[0]}
        elif albums:
            top_result = {'type': 'album', 'object': albums[0]}

    genres = Genre.objects.all()

    context = {
        'query': query,
        'songs': songs,
        'artists': artists,
        'albums': albums,
        'playlists': playlists,
        'top_result': top_result,
        'genres': genres,
    }
    return render(request, 'search.html', context)

def genre_detail(request, slug):
    genre = get_object_or_404(Genre, slug=slug)
    songs = Song.objects.filter(genre=genre).select_related('artist', 'album')
    albums = Album.objects.filter(genre=genre).select_related('artist')
    return render(request, 'genre_detail.html', {
        'genre': genre,
        'songs': songs,
        'albums': albums,
    })

def album_detail(request, album_id):
    album = get_object_or_404(Album, id=album_id)
    songs = album.songs.all().select_related('artist')
    total_duration_sec = sum(s.duration_seconds for s in songs)
    total_minutes = total_duration_sec // 60
    more_by_artist = Album.objects.filter(artist=album.artist).exclude(id=album.id)[:4]

    return render(request, 'album_detail.html', {
        'album': album,
        'songs': songs,
        'total_minutes': total_minutes,
        'more_by_artist': more_by_artist,
    })

def artist_detail(request, artist_id):
    artist = get_object_or_404(Artist, id=artist_id)
    top_songs = artist.songs.all().order_by('-plays_count')[:8]
    albums = artist.albums.all()

    return render(request, 'artist_detail.html', {
        'artist': artist,
        'top_songs': top_songs,
        'albums': albums,
    })

def playlist_detail(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id)
    songs = playlist.songs.all().select_related('artist', 'album')
    total_duration_sec = sum(s.duration_seconds for s in songs)
    total_minutes = total_duration_sec // 60

    available_songs = []
    if request.user.is_authenticated and playlist.user == request.user:
        available_songs = Song.objects.exclude(id__in=songs.values_list('id', flat=True))[:8]

    return render(request, 'playlist_detail.html', {
        'playlist': playlist,
        'songs': songs,
        'total_minutes': total_minutes,
        'available_songs': available_songs,
        'is_owner': request.user == playlist.user,
    })

def library(request):
    if not request.user.is_authenticated:
        return redirect('login')
    playlists = Playlist.objects.filter(user=request.user)
    liked_count = Favorite.objects.filter(user=request.user).count()
    return render(request, 'library.html', {
        'playlists': playlists,
        'liked_count': liked_count,
    })

def liked_songs(request):
    if not request.user.is_authenticated:
        return redirect('login')
    favorites = Favorite.objects.filter(user=request.user).select_related('song', 'song__artist', 'song__album')
    songs = [fav.song for fav in favorites]
    total_duration_sec = sum(s.duration_seconds for s in songs)
    total_minutes = total_duration_sec // 60

    return render(request, 'liked_songs.html', {
        'songs': songs,
        'total_minutes': total_minutes,
    })

@login_required
def create_playlist(request):
    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        description = request.POST.get('description', '').strip()
        cover_image_url = request.POST.get('cover_image_url', '').strip()
        if not title:
            title = f"My Playlist #{Playlist.objects.filter(user=request.user).count() + 1}"

        playlist = Playlist.objects.create(
            title=title,
            description=description,
            user=request.user,
            cover_image_url=cover_image_url,
        )
        return redirect('playlist_detail', playlist_id=playlist.id)

    return render(request, 'create_playlist.html')

@login_required
def add_to_playlist(request, song_id):
    if request.method == 'POST':
        playlist_id = request.POST.get('playlist_id')
        if playlist_id:
            playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
            song = get_object_or_404(Song, id=song_id)
            playlist.songs.add(song)
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)


@login_required
def playlist_add_song(request, playlist_id, song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song = get_object_or_404(Song, id=song_id)
    playlist.songs.add(song)
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or f'/playlist/{playlist_id}/'
    return redirect(next_url)

@login_required
def playlist_remove_song(request, playlist_id, song_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    song = get_object_or_404(Song, id=song_id)
    playlist.songs.remove(song)
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or f'/playlist/{playlist_id}/'
    return redirect(next_url)

@login_required
def playlist_delete(request, playlist_id):
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    if request.method == 'POST':
        playlist.delete()
        return redirect('library')
    return redirect('playlist_detail', playlist_id=playlist_id)

def toggle_like(request, song_id):
    if not request.user.is_authenticated:
        return redirect(f'/login/?next={request.path}')
    song = get_object_or_404(Song, id=song_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, song=song)
    if not created:
        favorite.delete()
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or '/'
    return redirect(next_url)

def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    next_page = request.GET.get('next', '/')

    if request.method == 'POST':
        username_or_email = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=username_or_email, password=password)
        if not user:
            try:
                user_obj = User.objects.get(email=username_or_email)
                user = authenticate(request, username=user_obj.username, password=password)
            except User.DoesNotExist:
                pass

        if user is not None:
            login(request, user)
            return redirect(next_page if next_page else 'home')
        else:
            error = "Incorrect username or password."

    return render(request, 'auth/login.html', {'error': error, 'next': next_page})

def user_signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not username or not password:
            error = "Please fill in all required fields."
        elif password != confirm_password:
            error = "Passwords do not match."
        elif User.objects.filter(username=username).exists():
            error = "This username is already taken."
        elif email and User.objects.filter(email=email).exists():
            error = "An account with this email already exists."
        else:
            user = User.objects.create_user(username=username, email=email, password=password)
            login(request, user)
            return redirect('home')

    return render(request, 'auth/signup.html', {'error': error})

def user_logout(request):
    logout(request)
    return redirect('home')

def demo_login(request):
    demo_user, created = User.objects.get_or_create(
        username='demo_listener',
        defaults={'email': 'demo@spotifyclone.local'}
    )
    if created:
        demo_user.set_password('demo1234')
        demo_user.save()
    login(request, demo_user)
    return redirect('home')
