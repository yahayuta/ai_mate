import os
import logging
import requests
import time
import model_chat_log
from flask import Flask, request, send_file, render_template, jsonify
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
            current_timestamp = int(time.time())
            timestamp_string = str(current_timestamp)
            filepath = f'/tmp/{timestamp_string}_recorded_audio.mp3'
            audio_file.save(filepath)
            url = upload_to_bucket(timestamp_string, filepath, 'ai-mate')  # Upload to Google Cloud Storage
            print(url)
            speech_file_path = openai_voice_to_voice(timestamp_string, url)
            return send_file(speech_file_path, as_attachment=True)
    return {'status': 'error'}

# delete chat all logs
@app.route('/delete', methods=['GET'])
def delete_log():
    model_chat_log.delete_logs()
    return {'status': 'success'}

# show all chat logs
@app.route('/history', methods=['GET'])
def history():
    return jsonify(model_chat_log.get_logs())
    
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

# voice to voice
def openai_voice_to_voice(name, url):

    prompt = []

    # download voice file from storage
    response = requests.get(url, allow_redirects=True, stream=True)
    path = f"/tmp/{name}.mp3"
    with open(path, mode='wb') as f:
        f.write(response.content)

    # do STT
    audio_file = open(path, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    text_user = transcript.text

    print(text_user)
    prompt.append({"role": "system", "content": "あなたは人間なので口語で会話してください"})
    prompt.extend(model_chat_log.get_logs())
    text_prompt = f'あなたは人間として振る舞ってください/n回答は必ず口語調にしてください/n以下が話しかけられた内容です/n「{text_user}」'
    prompt.append({"role": "user", "content": text_prompt})

    print(prompt)

    # send voice message text to llm
    response = client.chat.completions.create(model="gpt-3.5-turbo", messages=prompt)
    text_assistant = response.choices[0].message.content

    print(text_assistant)

    # save chat logs
    model_chat_log.save_log("user", text_user)
    model_chat_log.save_log("assistant", text_assistant)

    # do TTS
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
