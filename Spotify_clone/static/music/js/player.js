
document.addEventListener("DOMContentLoaded", function () {

    // Music Player Elements
    const audio = document.getElementById("audio-player");
    const playPauseBtn = document.getElementById("play-pause");
    const progress = document.getElementById("progress");
    const currentSong = document.getElementById("current-song");
    const currentArtist = document.getElementById("current-artist");

    // Play Song Buttons
    const playButtons = document.querySelectorAll(".play-song");

    let currentButton = null;

    // Play and Pause Function
    function updatePlayButton() {
        if (playPauseBtn && audio) {
            playPauseBtn.textContent = audio.paused ? "▶" : "❚❚";
        }

        playButtons.forEach(function (button) {
            button.textContent =
                button === currentButton && !audio.paused
                    ? "❚❚ Pause"
                    : "▶ Play";
        });
    }

    // Play a Selected Song
    playButtons.forEach(function (button) {

        button.addEventListener("click", function () {

            const songSrc = button.dataset.src;
            const songTitle = button.dataset.title;
            const songArtist = button.dataset.artist;

            if (!audio || !songSrc) {
                return;
            }

            // Pause if the same song is already playing
            if (
                currentButton === button &&
                !audio.paused
            ) {
                audio.pause();
                updatePlayButton();
                return;
            }

            // Load a new song
            if (currentButton !== button) {
                audio.src = songSrc;
                currentButton = button;

                if (currentSong) {
                    currentSong.textContent = songTitle || "Unknown Song";
                }

                if (currentArtist) {
                    currentArtist.textContent = songArtist || "Unknown Artist";
                }

                if (progress) {
                    progress.value = 0;
                }
            }

            audio.play()
                .then(function () {
                    updatePlayButton();
                })
                .catch(function (error) {
                    console.error("Unable to play audio:", error);
                });
        });

    });

    // Main Play/Pause Button
    if (playPauseBtn && audio) {

        playPauseBtn.addEventListener("click", function () {

            if (!audio.src) {
                return;
            }

            if (audio.paused) {
                audio.play().catch(function (error) {
                    console.error("Unable to play audio:", error);
                });
            } else {
                audio.pause();
            }
        });
    }

    // Update Progress Bar
    if (audio && progress) {

        audio.addEventListener("timeupdate", function () {

            if (audio.duration && isFinite(audio.duration)) {
                progress.value =
                    (audio.currentTime / audio.duration) * 100;
            }
        });

        // Move to selected time
        progress.addEventListener("input", function () {

            if (audio.duration && isFinite(audio.duration)) {
                audio.currentTime =
                    (progress.value / 100) * audio.duration;
            }
        });
    }

    // Update Buttons When Audio Starts or Pauses
    if (audio) {
        audio.addEventListener("play", updatePlayButton);
        audio.addEventListener("pause", updatePlayButton);
        audio.addEventListener("ended", function () {
            updatePlayButton();

            if (progress) {
                progress.value = 0;
            }
        });
    }

    // Song Search Functionality
    const songSearch = document.getElementById("song-search");

    if (songSearch) {

        songSearch.addEventListener("input", function () {

            const searchValue = this.value.toLowerCase().trim();
            const songCards = document.querySelectorAll(".song-item");

            let visibleSongs = 0;

            songCards.forEach(function (card) {

                const songName =
                    card.querySelector("h3")?.textContent.toLowerCase() || "";

                const artistName =
                    card.querySelector("p")?.textContent.toLowerCase() || "";

                if (
                    songName.includes(searchValue) ||
                    artistName.includes(searchValue)
                ) {
                    card.style.display = "";
                    visibleSongs++;
                } else {
                    card.style.display = "none";
                }
            });

            const noSongs = document.getElementById("no-songs");

            if (noSongs) {
                noSongs.style.display =
                    visibleSongs === 0 ? "block" : "none";
            }
        });
    }

});
