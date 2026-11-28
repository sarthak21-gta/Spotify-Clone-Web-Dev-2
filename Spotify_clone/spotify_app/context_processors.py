from .models import Favorite, PlayHistory, Playlist, Song


def player_context(request):
    play_id = request.GET.get('play')
    current_song = None

    if play_id:
        current_song = Song.objects.filter(id=play_id).select_related('artist', 'album').first()
        if current_song:
            request.session['current_song_id'] = current_song.id
            request.session['player_queue'] = [current_song.id]
            request.session['player_index'] = 0
            if request.user.is_authenticated:
                PlayHistory.objects.create(user=request.user, song=current_song)
    elif request.session.get('current_song_id'):
        current_song = Song.objects.filter(
            id=request.session.get('current_song_id')
        ).select_related('artist', 'album').first()

    if request.user.is_authenticated:
        user_playlists = Playlist.objects.filter(user=request.user)
        liked_song_ids = list(
            Favorite.objects.filter(user=request.user).values_list('song_id', flat=True)
        )
    else:
        user_playlists = []
        liked_song_ids = []

    return {
        'current_song': current_song,
        'user_playlists': user_playlists,
        'liked_song_ids': liked_song_ids,
        'current_path': request.get_full_path(),
        'player_queue_ids': request.session.get('player_queue', []),
    }
