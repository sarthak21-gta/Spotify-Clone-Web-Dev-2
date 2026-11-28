from .models import Playlist, Song, PlayHistory


def player_context(request):
    play_id = request.GET.get('play')
    current_song = None

    if play_id:
        current_song = Song.objects.filter(id=play_id).select_related('artist', 'album').first()
        if current_song:
            request.session['current_song_id'] = current_song.id
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

    return {
        'current_song': current_song,
        'user_playlists': user_playlists,
    }
