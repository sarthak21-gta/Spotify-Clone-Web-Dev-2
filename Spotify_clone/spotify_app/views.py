from django.shortcuts import render


def home(request):
    return render(request, 'music/home.html')
def songs(request):
    return render(request, 'music/songs.html')
def song_detail(request, song_id):
    return render(request, 'music/song_detail.html', {'song_id': song_id})
def playlists(request):
    return render(request, 'music/playlists.html')
def login_view(request):
    return render(request, 'music/login.html')
def signup_view(request):
    return render(request, 'music/signup.html')
