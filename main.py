import os
import logging
import time
import model_chat_log
import subprocess
from flask import Flask, request, send_file, render_template, jsonify, Response, stream_with_context
from openai import OpenAI
import json
import uuid

OPENAI_TOKEN = os.environ.get('OPENAI_TOKEN', '')

app = Flask(__name__, static_folder='static', template_folder='templates')

client = OpenAI(api_key=OPENAI_TOKEN)

# open web interface
@app.route('/')
def index():
    return render_template('index.html')

# handle chat with llm
@app.route('/voice_chat', methods=['POST'])
def voice_chat():
    audio_file = request.files.get('audio_data')
    
    if audio_file:
        session_id = f"{int(time.time())}_{uuid.uuid4().hex[:6]}"
        filepath = f'/tmp/{session_id}_recorded_audio.mp3'
        audio_file.save(filepath)
        return {'status': 'success', 'session_id': session_id}
    
    print('no audio_file!')
    return {'status': 'error', 'message': 'No audio file found'}

@app.route('/listen', methods=['GET'])
def listen():
    session_id = request.args.get("session_id")
    if not session_id:
        return {'status': 'error', 'message': 'Missing session ID'}, 400
        
    filepath = f'/tmp/{session_id}_recorded_audio.mp3'
    if not os.path.exists(filepath):
        return {'status': 'error', 'message': 'Audio file not found'}, 404
        
    def generate():
        try:
            for chunk in openai_voice_to_voice_stream(filepath):
                if chunk:
                    yield chunk
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)
                
    return Response(stream_with_context(generate()), mimetype="audio/mpeg")

# delete chat all logs
@app.route('/delete', methods=['GET'])
def delete_log():
    model_chat_log.delete_logs()
    return {'status': 'success'}

# show all chat logs
@app.route('/history', methods=['GET'])
def history():
    return jsonify(model_chat_log.get_logs())

# run streamlit app
@app.route('/run_streamlit', methods=['GET'])
def run_streamlit():
    subprocess.Popen(['streamlit', 'run', 'app_streamlit.py'])
    return {'status': 'success'}

# voice to voice streaming generator
def openai_voice_to_voice_stream(filepath):
    prompt = []

    # do STT
    with open(filepath, "rb") as audio_file:
        transcript = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
    text_user = transcript.text

    # Load Persona from file
    default_persona = "あなたは人間なので口語で会話してください"
    current_persona = default_persona
    if os.path.exists("persona.json"):
        try:
            with open("persona.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                current_persona = data.get("system_prompt", default_persona)
        except Exception as e:
            print(f"Failed to load persona: {e}")

    # making prompt with history
    print(text_user)
    prompt.append({"role": "system", "content": current_persona})
    prompt.extend(model_chat_log.get_logs())
    text_prompt = f'{current_persona}\n以下が話しかけられた内容です\n「{text_user}」'
    prompt.append({"role": "user", "content": text_prompt})

    print(prompt)

    # stream voice message text from llm
    response = client.chat.completions.create(model="gpt-5.4-mini", messages=prompt, stream=True)
    
    text_assistant = ""
    sentence_buffer = ""
    delimiters = [".", "?", "!", "。", "？", "！", "\n"]

    for chunk in response:
        if not chunk.choices:
            continue
            
        token = chunk.choices[0].delta.content
        if token:
            sentence_buffer += token
            text_assistant += token
            
            # Synthesize sentence_buffer if delimiter reached or arbitrarily long
            if any(dl in token for dl in delimiters) or len(sentence_buffer) > 80:
                tts_text = sentence_buffer.strip()
                sentence_buffer = ""
                
                if tts_text:
                    audio_response = client.audio.speech.create(
                        model="tts-1", 
                        voice="nova", 
                        input=tts_text,
                        response_format="mp3"
                    )
                    for audio_chunk in audio_response.iter_bytes(chunk_size=4096):
                        yield audio_chunk

    # Process remaining text (if any)
    tts_text = sentence_buffer.strip()
    if tts_text:
        audio_response = client.audio.speech.create(
            model="tts-1", 
            voice="nova", 
            input=tts_text,
            response_format="mp3"
        )
        for audio_chunk in audio_response.iter_bytes(chunk_size=4096):
            yield audio_chunk

    print(text_assistant)

    # save chat logs
    model_chat_log.save_log("user", text_user)
    model_chat_log.save_log("assistant", text_assistant)

if __name__ != '__main__':
    # if we are not running directly, we set the loggers
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=True)
