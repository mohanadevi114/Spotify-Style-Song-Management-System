// ==========================================
// Spotify Clone - Audio Playback & Controller
// ==========================================

document.addEventListener('DOMContentLoaded', () => {
    console.log("Spotify JS Script Loaded Successfully!");
});

/**
 * Plays the selected audio file using the persistent player at the bottom.
 * @param {string} audioPath - Relative path from database (e.g., 'songs/mehabooba.mp3')
 * @param {string} songName - Name of the song to display
 */
function playAudio(audioPath, songName) {
    const audioPlayer = document.getElementById('main-audio-player');
    const audioSource = document.getElementById('audio-source');
    const songTitleDisplay = document.getElementById('current-song-title');

    // Check if player components exist
    if (!audioPlayer || !audioSource) {
        console.error("Error: Audio player HTML elements not found!");
        alert("Audio player HTML elements missing in templates!");
        return;
    }

    if (!audioPath || audioPath.trim() === '') {
        console.error("Error: Audio path is empty!");
        alert("Audio path not specified for this song.");
        return;
    }

    // Ensure proper path construction with leading slash
    // Example output: /static/songs/mehabooba.mp3
    let cleanPath = audioPath.startsWith('/') ? audioPath : '/' + audioPath;
    if (!cleanPath.startsWith('/static/')) {
        cleanPath = '/static' + cleanPath;
    }

    // Update source and UI title
    audioSource.src = cleanPath;
    if (songTitleDisplay) {
        songTitleDisplay.innerText = "Now Playing: " + (songName || "Unknown Track");
    }

    // Reload audio element with new source and trigger playback
    audioPlayer.load();
    
    const playPromise = audioPlayer.play();
    if (playPromise !== undefined) {
        playPromise
            .then(() => {
                console.log("Now playing:", cleanPath);
            })
            .catch(error => {
                console.error("Playback Error:", error);
                alert("Playback failed! File format or path issue: " + cleanPath);
            });
    }
}

/**
 * Utility function to toggle play/pause from external UI controls if needed
 */
function togglePlayPause() {
    const audioPlayer = document.getElementById('main-audio-player');
    if (!audioPlayer) return;

    if (audioPlayer.paused) {
        audioPlayer.play();
    } else {
        audioPlayer.pause();
    }
}