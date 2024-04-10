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

    document.getElementById("deleteLogs").addEventListener("click", () => {
        fetch("/delete")
            .then(response => response.json())
            .then(data => {
                console.log(data);
                document.getElementById("responseArea").innerHTML = data.status;
            });
    });
    
    document.getElementById("showHistory").addEventListener("click", () => {
        fetch("/history")
        .then(response => response.json())
        .then(data => {
            let readableMessages = data.map((msg, index) => {
                return `role:${msg.role} content:${msg.content}<br>`;
            }).join('');
            document.getElementById("responseArea").innerHTML = readableMessages;
        });
    });
});
