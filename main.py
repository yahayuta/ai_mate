import os
import logging
import requests
import time
from flask import Flask, request, send_file, render_template
from google.cloud import storage
from openai import OpenAI

OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN', '')

app = Flask(__name__, static_folder='static', template_folder='templates')

client = OpenAI(api_key=OPENAI_TOKEN)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record', methods=['POST'])
def save_audio():
    if request.method == 'POST':
        audio_file = request.files['audio_data']
        if audio_file:
            static_dir = 'static'
            if not os.path.exists(static_dir):
                os.makedirs(static_dir)  # Create the static directory if it doesn't exist
            filename = 'recorded_audio.mp3'
            filepath = os.path.join(static_dir, filename)
            audio_file.save(filepath)  # Save in static folder
            current_timestamp = int(time.time())
            timestamp_string = str(current_timestamp)
            url = upload_to_bucket(timestamp_string, filepath, 'ai-mate')  # Upload to Google Cloud Storage
            print(url)
            speech_file_path = openai_voice_to_voice(timestamp_string, url)
            return send_file(speech_file_path, as_attachment=True)
    return {'status': 'error'}

@app.route('/play', methods=['GET'])
def play_audio():
    return send_file(os.path.join('static', 'recorded_audio.mp3'), as_attachment=True)

#  Uploads a file to the Google Cloud Storage bucket
def upload_to_bucket(blob_name, file_path, bucket_name):
    # Create a Cloud Storage client
    storage_client = storage.Client()

    # Get the bucket that the file will be uploaded to
    bucket = storage_client.bucket(bucket_name)

    # Create a new blob and upload the file's content
    blob = bucket.blob(blob_name)
    blob.upload_from_filename(file_path)

    # Make the blob publicly viewable
    blob.make_public()

    # Return the public URL of the uploaded file
    return blob.public_url

# 音声TO音声
def openai_voice_to_voice(name, url):

    prompt = []

    # Slackからの音声ファイルダウンロード実施
    response = requests.get(url, allow_redirects=True, stream=True)
    path = f"/tmp/{name}.mp3"
    with open(path, mode='wb') as f:
        f.write(response.content)

    # 音声ファイルを文字起こしする
    audio_file = open(path, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    text_user = transcript.text

    print(text_user)
    prompt.append({"role": "system", "content": "あなたは人間なので口語で会話してください"})
    prompt.append({"role": "user", "content": text_user})

    print(prompt)

    # 文字起こししたテキストをAIに送信する
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=prompt)
    text_assistant = response.choices[0].message.content

    print(text_assistant)

    # AIの回答を音声に変換する
    response = client.audio.speech.create(model="tts-1", voice="nova", input=text_assistant)

    speech_file_path = f"/tmp/{name}_speech.mp3"
    response.stream_to_file(speech_file_path)

    return speech_file_path

if __name__ != '__main__':
    # if we are not running directly, we set the loggers
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
