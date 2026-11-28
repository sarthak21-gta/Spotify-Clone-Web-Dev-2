<<<<<<< HEAD
from .models import Playlist, Song, PlayHistory

=======
from .models import Playlist, Song, Favorite
>>>>>>> 4be12555d5d355c1b4d869787a5a013d0cb899e5

def player_context(request):
    play_id = request.GET.get('play')
    if play_id:
        current_song = Song.objects.filter(id=play_id).select_related('artist', 'album').first()
        if current_song:
            request.session['current_song_id'] = current_song.id
<<<<<<< HEAD
            # Record play in history for authenticated users
            if request.user.is_authenticated:
                PlayHistory.objects.create(user=request.user, song=current_song)
    elif request.session.get('current_song_id'):
        current_song = Song.objects.filter(
            id=request.session['current_song_id']
        ).select_related('artist', 'album').first()

    user_playlists = (
        Playlist.objects.filter(user=request.user)
        if request.user.is_authenticated
        else []
    )
=======
            request.session['player_queue'] = [current_song.id]
            request.session['player_index'] = 0
    else:
        current_song = Song.objects.filter(id=request.session.get('current_song_id')).select_related('artist', 'album').first()
>>>>>>> 4be12555d5d355c1b4d869787a5a013d0cb899e5

    user_playlists = Playlist.objects.filter(user=request.user) if request.user.is_authenticated else []
    liked_song_ids = list(Favorite.objects.filter(user=request.user).values_list('song_id', flat=True)) if request.user.is_authenticated else []
    return {
        'current_song': current_song,
        'user_playlists': user_playlists,
        'liked_song_ids': liked_song_ids,
        'current_path': request.get_full_path(),
        'player_queue_ids': request.session.get('player_queue', []),
    }
