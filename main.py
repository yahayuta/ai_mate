import os
import logging
import time
import model_chat_log
from flask import Flask, request, send_file, render_template, jsonify
from openai import OpenAI

OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN', '')

app = Flask(__name__, static_folder='static', template_folder='templates')

client = OpenAI(api_key=OPENAI_TOKEN)

# open web interface
@app.route('/')
def index():
    return render_template('index.html')

# handle chat with llm
@app.route('/record', methods=['POST'])
def save_audio():
    if request.method == 'POST':
        audio_file = request.files['audio_data']
        if audio_file:
            current_timestamp = int(time.time())
            timestamp_string = str(current_timestamp)
            filepath = f'/tmp/{timestamp_string}_recorded_audio.mp3'
            audio_file.save(filepath)
            speech_file_path = openai_voice_to_voice(timestamp_string)
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

# voice to voice
def openai_voice_to_voice(name):

    prompt = []

    # do STT
    path = f'/tmp/{name}_recorded_audio.mp3'
    audio_file = open(path, "rb")
    transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    text_user = transcript.text

    # making prompt with history
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
