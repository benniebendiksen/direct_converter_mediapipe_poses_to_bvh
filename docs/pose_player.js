// pose_player.js - Load and play stored MediaPipe landmarks

let storedPoseData = null;
let currentFrameIndex = 0;
let isPlayingStored = false;
let playbackInterval = null;
let loopPlayback = false; // Option to loop

// Track which JSON we are using (default fallback)
let storedPoseJsonPath = './pose_output.json';

// Load pose JSON (can be dynamic)
async function loadStoredPoses(jsonUrl) {
    try {
        // Prefer explicit argument, then global set by index.html, then fallback
        const baseUrl =
            jsonUrl ||
            window.__currentPoseJsonPath ||
            storedPoseJsonPath ||
            './pose_output.json';

        storedPoseJsonPath = baseUrl; // remember last used

        // Cache-bust so we never get stale pose data
        const url =
            baseUrl + (baseUrl.includes('?') ? '&' : '?') + 'ts=' + Date.now();

        console.log('Loading pose JSON from:', url);

        const response = await fetch(url, { cache: 'no-store' });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        storedPoseData = await response.json();
        console.log(`Loaded ${storedPoseData.length} frames of pose data from ${baseUrl}`);

        const statusEl = document.getElementById('playbackStatus');
        if (statusEl) {
            statusEl.textContent = `Loaded ${storedPoseData.length} frames from ${baseUrl} - Ready to play`;
        }

        return true;
    } catch (error) {
        console.error('Error loading pose JSON:', error);
        const statusEl = document.getElementById('playbackStatus');
        if (statusEl) {
            statusEl.textContent = 'Error: pose JSON not found';
        }
        return false;
    }
}

// Convert stored landmark array to MediaPipe format
function convertToMediaPipeFormat(landmarkArray) {
    return landmarkArray.map((lm) => ({
        x: lm.x,
        y: lm.y,
        z: lm.z,
        visibility: lm.visibility || 1.0
    }));
}

// Check if we should auto-stop recording when playback ends
function checkAutoStopRecording() {
    if (window.recording && !isPlayingStored) {
        console.log('Playback ended - auto-stopping recording');
        if (window.stopRecording) {
            window.stopRecording();
        }
        const recordBtn = document.getElementById('recordButton');
        if (recordBtn && recordBtn.textContent.includes('Stop')) {
            recordBtn.click();
        }
    }
}

function playStoredPoses(loop = false) {
    if (!storedPoseData || storedPoseData.length === 0) {
        alert('Please load pose JSON first');
        return;
    }

    // Stop live camera feed if it exists (from your earlier fix)
    if (window.mpCamera) {
        console.log("Stopping live camera feed for playback.");
        window.mpCamera.stop();
    }
    if (window.holistic) {
        console.log("Disabling live results callback.");
        window.holistic.onResults(() => {}); // disable overwrites
    }

    // Automatically start recording when playback begins
    if (window.toggleRecording) {
        window.toggleRecording(true); // bypass alert
    }

    loopPlayback = loop;
    isPlayingStored = true;
    currentFrameIndex = 0;

    console.log(`Starting playback (${loop ? 'loop mode' : 'once'}) from JSON: ${storedPoseJsonPath}`);

    playbackInterval = setInterval(() => {
        if (currentFrameIndex >= storedPoseData.length) {
            if (loopPlayback) {
                currentFrameIndex = 0;
            } else {
                stopStoredPoses();
                checkAutoStopRecording();
                return;
            }
        }

        // This is the ONLY source for holisticResults during playback
        window.holisticResults = {
            poseLandmarks: convertToMediaPipeFormat(storedPoseData[currentFrameIndex])
        };

        // Signal to BVH recorder that a frame should be recorded
        window.shouldRecordFrame = true;

        currentFrameIndex++;

        const statusEl = document.getElementById('playbackStatus');
        if (statusEl) {
            const loopText = loopPlayback ? ' (looping)' : '';
            statusEl.textContent = `Playing frame ${currentFrameIndex}/${storedPoseData.length}${loopText}`;
        }
    }, 1000 / 30); // 30fps
}

function stopStoredPoses() {
    isPlayingStored = false;
    if (playbackInterval) {
        clearInterval(playbackInterval);
        playbackInterval = null;
    }

    window.holisticResults = null;

    // Restore live callbacks / camera if they exist
    if (window.holistic && window.onResults2) {
        console.log("Restoring live results callback.");
        window.holistic.onResults(window.onResults2);
    }
    if (window.mpCamera) {
        console.log("Restarting live camera feed.");
        window.mpCamera.start();
    }

    const statusEl = document.getElementById('playbackStatus');
    if (statusEl && storedPoseData) {
        statusEl.textContent = `Stopped at frame ${currentFrameIndex}/${storedPoseData.length}`;
    }

    console.log('Stopped playback');
}

function resetStoredPoses() {
    stopStoredPoses();
    currentFrameIndex = 0;
    window.holisticResults = null;

    const statusEl = document.getElementById('playbackStatus');
    if (statusEl && storedPoseData) {
        statusEl.textContent = `Reset - Ready to play ${storedPoseData.length} frames`;
    }
}

function toggleLoop() {
    loopPlayback = !loopPlayback;
    console.log(`Loop mode: ${loopPlayback ? 'ON' : 'OFF'}`);

    const loopBtn = document.getElementById('loopBtn');
    if (loopBtn) {
        if (loopPlayback) {
            loopBtn.classList.remove('grey');
            loopBtn.classList.add('green');
        } else {
            loopBtn.classList.remove('green');
            loopBtn.classList.add('grey');
        }
    }

    if (isPlayingStored) {
        stopStoredPoses();
        playStoredPoses(loopPlayback);
    }
}

// Called from index.html when a new JSON is created by the backend
async function setPoseJson(jsonUrl) {
    console.log("posePlayer.setPoseJson called with:", jsonUrl);
    storedPoseJsonPath = jsonUrl;
    window.__currentPoseJsonPath = jsonUrl;
    await loadStoredPoses(jsonUrl);
}

// On script load: if index already set __currentPoseJsonPath, use that; else fallback
(async () => {
    if (window.__currentPoseJsonPath) {
        console.log("pose_player.js: found __currentPoseJsonPath on load:", window.__currentPoseJsonPath);
        await setPoseJson(window.__currentPoseJsonPath);
    } else {
        console.log("pose_player.js: no __currentPoseJsonPath yet, loading default JSON");
        await loadStoredPoses();
    }
})();

// Export functions for UI controls
window.posePlayer = {
    load: loadStoredPoses,
    play: playStoredPoses,
    stop: stopStoredPoses,
    reset: resetStoredPoses,
    toggleLoop: toggleLoop,
    isPlaying: () => isPlayingStored,
    setPoseJson: setPoseJson   // 👈 used from index.html
};
