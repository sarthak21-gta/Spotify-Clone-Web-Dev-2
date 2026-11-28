from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Song, Album, Artist, Playlist, Genre, Favorite, PlayHistory, ArtistFollow, UserProfile

def home(request):
    featured_playlists = Playlist.objects.filter(is_public=True)[:6]
    popular_albums = Album.objects.all().order_by('-release_date')[:6]
    popular_artists = Artist.objects.all().order_by('-monthly_listeners')[:6]
    trending_songs = Song.objects.filter(is_trending=True)[:10]
    if not trending_songs:
        trending_songs = Song.objects.all()[:10]
    
    genres = Genre.objects.all()[:6]

    quick_picks = list(popular_albums[:4]) + list(featured_playlists[:2])

    # Recently Played & Recommendations for authenticated users
    recently_played = []
    recommended_songs = []
    recently_played_song_ids = set()

    if request.user.is_authenticated:
        # Get unique recently-played songs (most recent first, deduplicated)
        seen_ids = set()
        for ph in PlayHistory.objects.filter(user=request.user).select_related('song', 'song__artist', 'song__album')[:50]:
            if ph.song_id not in seen_ids:
                seen_ids.add(ph.song_id)
                recently_played.append(ph.song)
            if len(recently_played) >= 6:
                break
        recently_played_song_ids = seen_ids

        # Recommendations: songs from same genres/artists as recently played, not already played
        if recently_played:
            played_genre_ids = [s.genre_id for s in recently_played if s.genre_id]
            played_artist_ids = [s.artist_id for s in recently_played]
            recommended_songs = (
                Song.objects.filter(
                    Q(genre_id__in=played_genre_ids) | Q(artist_id__in=played_artist_ids)
                )
                .exclude(id__in=recently_played_song_ids)
                .select_related('artist', 'album')
                .order_by('-plays_count')[:6]
            )
        else:
            # Fallback: show popular songs if no history
            recommended_songs = Song.objects.filter(is_popular=True).select_related('artist', 'album')[:6]
            if not recommended_songs:
                recommended_songs = Song.objects.all().order_by('-plays_count').select_related('artist', 'album')[:6]

    context = {
        'quick_picks': quick_picks,
        'featured_playlists': featured_playlists,
        'popular_albums': popular_albums,
        'popular_artists': popular_artists,
        'trending_songs': trending_songs,
        'genres': genres,
        'recently_played': recently_played,
        'recommended_songs': recommended_songs,
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
    follower_count = artist.followers.count()
    is_following = (
        request.user.is_authenticated and
        ArtistFollow.objects.filter(user=request.user, artist=artist).exists()
    )

    return render(request, 'artist_detail.html', {
        'artist': artist,
        'top_songs': top_songs,
        'albums': albums,
        'follower_count': follower_count,
        'is_following': is_following,
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


def toggle_follow(request, artist_id):
    """Toggle following an artist. Returns to referer or artist page."""
    if not request.user.is_authenticated:
        return redirect(f'/login/?next=/artist/{artist_id}/')
    artist = get_object_or_404(Artist, id=artist_id)
    follow, created = ArtistFollow.objects.get_or_create(user=request.user, artist=artist)
    if not created:
        follow.delete()
    # Ensure the user has a profile
    UserProfile.objects.get_or_create(user=request.user)
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or f'/artist/{artist_id}/'
    return redirect(next_url)


def user_profile(request, username):
    """Public user profile page."""
    profile_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=profile_user)

    if not profile.is_public and request.user != profile_user:
        return render(request, 'profile_private.html', {'profile_user': profile_user})

    playlists = Playlist.objects.filter(user=profile_user, is_public=True).order_by('-created_at')
    liked_count = Favorite.objects.filter(user=profile_user).count()
    following_artists = ArtistFollow.objects.filter(user=profile_user).select_related('artist').order_by('-followed_at')

    # Recent play history (deduplicated, up to 6)
    seen = set()
    recent_tracks = []
    for ph in PlayHistory.objects.filter(user=profile_user).select_related('song', 'song__artist', 'song__album')[:40]:
        if ph.song_id not in seen:
            seen.add(ph.song_id)
            recent_tracks.append(ph.song)
        if len(recent_tracks) >= 6:
            break

    is_own_profile = request.user == profile_user

    return render(request, 'user_profile.html', {
        'profile_user': profile_user,
        'profile': profile,
        'playlists': playlists,
        'liked_count': liked_count,
        'following_artists': following_artists,
        'recent_tracks': recent_tracks,
        'is_own_profile': is_own_profile,
    })


@login_required
def edit_profile(request):
    """Edit the logged-in user's own profile."""
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        profile.bio = request.POST.get('bio', '').strip()
        profile.avatar_url = request.POST.get('avatar_url', '').strip()
        profile.is_public = request.POST.get('is_public') == 'on'
        profile.save()
        return redirect('user_profile', username=request.user.username)
    return render(request, 'edit_profile.html', {'profile': profile})

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

@login_required
def recently_played_view(request):
    """Full Recently Played page with play history."""
    # Deduplicated recently played songs, most recent first
    seen_ids = []
    seen_set = set()
    for ph in PlayHistory.objects.filter(user=request.user).select_related('song', 'song__artist', 'song__album'):
        if ph.song_id not in seen_set:
            seen_set.add(ph.song_id)
            seen_ids.append(ph)
        if len(seen_ids) >= 50:
            break

    # Recommendations: genres & artists from last 10 played
    recent_songs = [ph.song for ph in seen_ids[:10]]
    played_genre_ids = [s.genre_id for s in recent_songs if s.genre_id]
    played_artist_ids = [s.artist_id for s in recent_songs]
    recommended = (
        Song.objects.filter(
            Q(genre_id__in=played_genre_ids) | Q(artist_id__in=played_artist_ids)
        )
        .exclude(id__in=seen_set)
        .select_related('artist', 'album')
        .order_by('-plays_count')[:12]
    )
    if not recommended:
        recommended = Song.objects.exclude(id__in=seen_set).order_by('-plays_count').select_related('artist', 'album')[:12]

    return render(request, 'recently_played.html', {
        'history_entries': seen_ids,
        'recommended_songs': recommended,
    })


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


# ---------------------------------------------------------------------------
# AJAX music player API
# ---------------------------------------------------------------------------
def _song_payload(song):
    return {
        'id': song.id,
        'title': song.title,
        'artist': song.artist.name,
        'artist_url': f'/artist/{song.artist_id}/',
        'cover_url': song.get_cover_url(),
        'audio_url': song.get_audio_url(),
        'duration': song.duration_seconds,
    }

def player_play(request):
    """Start a song and save its queue in the user's session."""
    from django.http import JsonResponse
    import json
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body or '{}')
        song_id = int(data.get('song_id'))
        queue_ids = [int(value) for value in data.get('queue', [])]
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Invalid song or queue'}, status=400)
    song = get_object_or_404(Song.objects.select_related('artist', 'album'), id=song_id)
    valid_ids = list(Song.objects.filter(id__in=queue_ids).values_list('id', flat=True))
    if song.id not in valid_ids:
        valid_ids.insert(0, song.id)
    request.session['player_queue'] = valid_ids
    request.session['player_index'] = valid_ids.index(song.id)
    request.session['current_song_id'] = song.id
    song.plays_count += 1
    song.save(update_fields=['plays_count'])
    return JsonResponse({'song': _song_payload(song), 'queue': valid_ids, 'index': request.session['player_index']})

def player_step(request):
    """Move through the session queue without reloading the page."""
    from django.http import JsonResponse
    import json, random
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    try:
        data = json.loads(request.body or '{}')
    except json.JSONDecodeError:
        data = {}
    queue_ids = request.session.get('player_queue', [])
    if not queue_ids:
        return JsonResponse({'error': 'Queue is empty'}, status=404)
    index = int(request.session.get('player_index', 0))
    action = data.get('action', 'next')
    repeat_all = bool(data.get('repeat_all'))
    shuffle = bool(data.get('shuffle'))
    if action == 'previous':
        index = max(0, index - 1)
    elif shuffle and len(queue_ids) > 1:
        choices = [i for i in range(len(queue_ids)) if i != index]
        index = random.choice(choices)
    elif index + 1 < len(queue_ids):
        index += 1
    elif repeat_all:
        index = 0
    else:
        return JsonResponse({'ended': True})
    song = get_object_or_404(Song.objects.select_related('artist', 'album'), id=queue_ids[index])
    request.session['player_index'] = index
    request.session['current_song_id'] = song.id
    song.plays_count += 1
    song.save(update_fields=['plays_count'])
    return JsonResponse({'song': _song_payload(song), 'index': index, 'queue': queue_ids})

@login_required

def ajax_toggle_like(request, song_id):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    song = get_object_or_404(Song, id=song_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, song=song)
    if not created:
        favorite.delete()
    return JsonResponse({'liked': created, 'song_id': song.id})

@login_required

def ajax_add_to_playlist(request, song_id):
    from django.http import JsonResponse
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    song = get_object_or_404(Song, id=song_id)
    playlist_id = request.POST.get('playlist_id')
    playlist = get_object_or_404(Playlist, id=playlist_id, user=request.user)
    playlist.songs.add(song)
    return JsonResponse({'success': True, 'playlist': playlist.title, 'song_id': song.id})
