# Spotify Clone – Continuous Playback & AJAX Updates

This version adds a persistent audio player, a session-based play queue, next/previous, shuffle, repeat (off/all/one), AJAX likes, AJAX add-to-playlist, and fetch-based page navigation that keeps the player mounted.

## Run in VS Code
1. Open the `Spotify_clone` folder (the folder containing `manage.py`).
2. Create/activate a virtual environment.
3. Install Django: `python -m pip install django`.
4. Run migrations: `python manage.py migrate`.
5. Start the server: `python manage.py runserver`.
6. Open `http://127.0.0.1:8000/`.

Audio playback requires each Song to have a working `audio_file` or `audio_url`. The project’s existing database is included in this ZIP; back it up before running migrations or changing data.

## Git
After testing: `git add .` then `git commit -m "Add continuous playback and AJAX navigation"` then `git push`.
