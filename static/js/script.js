let mediaRecorder;
let audioChunks = [];

navigator.mediaDevices.getUserMedia({ audio: true })
    .then(stream => {
        mediaRecorder = new MediaRecorder(stream);
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
        };
        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/mpeg-3' });
            const formData = new FormData();
            formData.append("audio_data", audioBlob);
            fetch("/record", { method: "POST", body: formData })
                .then(response => response.blob())
                .then(blob => {
                    const audioUrl = URL.createObjectURL(blob);
                    new Audio(audioUrl).play();
                });
            audioChunks = [];
        };
    });

document.addEventListener('DOMContentLoaded', function() {
    // Event listener for the checkbox change
    document.getElementById("recordCheckbox").addEventListener("change", () => {
        if (document.getElementById("recordCheckbox").checked) {
            mediaRecorder.start();
        } else {
            mediaRecorder.stop();
        }
    });
});

