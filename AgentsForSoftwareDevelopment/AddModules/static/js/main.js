// Helper function to extract video_id from various YouTube URL patterns
function extractVideoId(url) {
    const patterns = [
        /v=([^&]+)/,                 // Standard YouTube URL (e.g., ?v=ID)
        /youtu\.be\/([^?&]+)/,       // Shortened YouTube URL (e.g., youtu.be/ID)
        /youtube\.com\/live\/([^?&]+)/ // YouTube Live URL (e.g., youtube.com/live/ID)
    ];
    for (const pattern of patterns) {
        const match = url.match(pattern);
        if (match) {
            return match[1]; // Return first matched group
        }
    }
    return null; // Return null if no match is found
}


// Update info display on a page load
function window_onload() {
    const urlParams = new URLSearchParams(window.location.search);
    const videoId = urlParams.get('v');
    const startTime = urlParams.get('t') || 0;

    if (videoId) {
        const url = `https://www.youtube.com/watch?v=${videoId}`;
        const urlElement = document.getElementById('currentUrl');
        urlElement.textContent = url;
        urlElement.href = url;
    }
}

function update_info(e) {
    e.preventDefault();
    const videoUrl = document.getElementById('videoUrl').value.trim();
    const startTime = document.getElementById('startTime').value || 0;

    // Extract the video_id using the helper function
    const videoId = extractVideoId(videoUrl);

    if (videoId) {
        const youtubeUrl = `https://www.youtube.com/watch?v=${videoId}&t=${startTime}`;
        const urlElement = document.getElementById('currentUrl');
        urlElement.textContent = youtubeUrl;
        urlElement.href = youtubeUrl;

        // Update iframe src directly to start playing immediately
        const iframe = document.getElementById('videoFrame');
        iframe.src = `https://www.youtube.com/embed/${videoId}?start=${startTime}&rel=0&autoplay=1`;
    } else {
        alert('Please enter a valid YouTube URL');
    }
}
