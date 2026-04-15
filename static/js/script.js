let mediaRecorder;
let audioChunks = [];
let isRecording = false;

document.addEventListener('DOMContentLoaded', function() {
    const micBtn = document.getElementById('micBtn');
    const glowRing = document.getElementById('glowRing');
    const statusText = document.getElementById('statusText');
    const audioPlayer = document.getElementById('audioPlayer');
    const aiAvatar = document.getElementById('aiAvatar');

    // UI Buttons
    const deleteLogsBtn = document.getElementById('deleteLogs');
    const runStreamlitBtn = document.getElementById('runStreamlit');
    const showHistoryBtn = document.getElementById('showHistory');
    const voiceSelect = document.getElementById('voiceSelect'); // Added voice selector

    // Request permissions early
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(stream => {
            mediaRecorder = new MediaRecorder(stream);
            
            mediaRecorder.ondataavailable = event => {
                audioChunks.push(event.data);
            };

            mediaRecorder.onstop = () => {
                statusText.innerText = "Thinking...";
                glowRing.classList.remove('active'); // Stop user record glow
                glowRing.style.background = "#3b82f6"; // Blueish for thinking
                glowRing.classList.add('active'); 

                const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg-3' });
                const formData = new FormData();
                formData.append("audio_data", audioBlob);
                
                // POST to backend
                fetch("/voice_chat", { method: "POST", body: formData })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            statusText.innerText = "AI Speaking...";
                            glowRing.style.background = "#8b5cf6"; // Purple glow for AI
                            
                            // Point audio player to the streaming GET endpoint
                            const selectedVoice = voiceSelect ? voiceSelect.value : 'nova';
                            audioPlayer.src = `/listen?session_id=${data.session_id}&voice=${selectedVoice}`;
                        } else {
                            statusText.innerText = "Error requesting response.";
                            glowRing.classList.remove('active');
                        }
                    })
                    .catch(err => {
                        console.error(err);
                        statusText.innerText = "Connection Failed";
                        glowRing.classList.remove('active');
                    });
                    
                audioChunks = [];
            };
        })
        .catch(err => {
            console.error("Microphone access denied:", err);
            statusText.innerText = "Mic access required!";
        });

    let talkingInterval = null;
    let isMouthOpen = false;

    // Handle Audio Playback animations
    audioPlayer.onplay = () => {
        glowRing.classList.add('active');
        if (aiAvatar) {
            aiAvatar.classList.add('talking');
            // Toggle mouth open and closed every 180ms
            talkingInterval = setInterval(() => {
                isMouthOpen = !isMouthOpen;
                aiAvatar.src = isMouthOpen ? '/static/images/avatar_open.png' : '/static/images/avatar.png';
            }, 180);
        }
    };
    audioPlayer.onended = () => {
        statusText.innerText = "Ready to listen...";
        glowRing.classList.remove('active');
        glowRing.style.background = "#8b5cf6"; // Reset color
        if (aiAvatar) {
            aiAvatar.classList.remove('talking');
            clearInterval(talkingInterval);
            aiAvatar.src = '/static/images/avatar.png';
            isMouthOpen = false;
        }
    };

    // Push to Talk Events (Mouse & Touch)
    const startRecording = (e) => {
        e.preventDefault();
        if(!mediaRecorder || mediaRecorder.state === 'recording') return;
        
        // Interrupt AI if it's currently speaking
        audioPlayer.pause();
        audioPlayer.src = "";

        isRecording = true;
        audioChunks = [];
        mediaRecorder.start();
        micBtn.classList.add('recording');
        glowRing.style.background = "#ef4444"; // Red for recording
        glowRing.classList.add('active');
        if (aiAvatar) {
            aiAvatar.classList.remove('talking');
            clearInterval(talkingInterval);
            aiAvatar.src = '/static/images/avatar.png';
            isMouthOpen = false;
        }
        statusText.innerText = "Listening...";
    };

    const stopRecording = (e) => {
        e.preventDefault();
        if(!isRecording) return;
        
        isRecording = false;
        micBtn.classList.remove('recording');
        if (mediaRecorder && mediaRecorder.state === 'recording') {
            mediaRecorder.stop();
        }
    };

    // Binding mouse and touch events for Push-To-Talk
    micBtn.addEventListener('mousedown', startRecording);
    micBtn.addEventListener('touchstart', startRecording, {passive: false});
    document.addEventListener('mouseup', stopRecording);
    document.addEventListener('touchend', stopRecording);

    // Sidebar Controls
    deleteLogsBtn.addEventListener("click", () => {
        statusText.innerText = "Clearing logs...";
        fetch("/delete")
            .then(response => response.json())
            .then(() => {
                statusText.innerText = "Logs Cleared!";
                setTimeout(() => statusText.innerText = "Ready to listen...", 2000);
            });
    });

    runStreamlitBtn.addEventListener("click", () => {
        fetch("/run_streamlit")
            .then(response => response.json())
            .then(() => {
                statusText.innerText = "Streamlit Admin Launched!";
                setTimeout(() => statusText.innerText = "Ready to listen...", 2000);
            });
    });
    
    showHistoryBtn.addEventListener("click", () => {
        statusText.innerText = "Check Browser Console for Logs";
        fetch("/history")
            .then(response => response.json())
            .then(data => {
                console.log("--- BIGQUERY CHAT HISTORY ---");
                console.table(data);
                setTimeout(() => statusText.innerText = "Ready to listen...", 2000);
            });
    });
});
