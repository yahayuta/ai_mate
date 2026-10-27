import base64
import os

import pytest

import main
import model_chat_log

FETCH = {"X-Requested-With": "fetch"}


def basic(password, user="mate"):
    return {"Authorization": "Basic " + base64.b64encode(f"{user}:{password}".encode()).decode()}


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "pw-test")
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.setattr(model_chat_log, "get_logs", lambda: [{"role": "user", "content": "hi"}])
    monkeypatch.setattr(model_chat_log, "delete_logs", lambda: None)
    return main.app.test_client()


@pytest.mark.parametrize("method,path", [
    ("get", "/"), ("get", "/history"), ("get", "/listen?session_id=1_abcdef"),
    ("post", "/delete"), ("post", "/voice_chat"), ("post", "/run_streamlit"),
    ("get", "/static/js/script.js"),
])
def test_every_route_requires_password(client, method, path):
    assert getattr(client, method)(path).status_code == 401
    assert getattr(client, method)(path, headers={**basic("wrong"), **FETCH}).status_code == 401


def test_page_and_history_with_password(client):
    assert client.get("/", headers=basic("pw-test")).status_code == 200
    r = client.get("/history", headers=basic("pw-test"))
    assert r.status_code == 200 and r.get_json() == [{"role": "user", "content": "hi"}]


def test_cloud_run_without_password_stays_open_with_warning(client, monkeypatch, capsys):
    monkeypatch.setenv("APP_PASSWORD", "")
    monkeypatch.setenv("K_SERVICE", "ai-mate")
    assert client.get("/history").status_code == 200
    assert "APP_PASSWORD is not set" in capsys.readouterr().out


def test_fetch_header_still_required_without_password(client, monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "")
    assert client.post("/delete").status_code == 403
    assert client.post("/delete", headers=FETCH).status_code == 200


def test_local_run_without_password_is_allowed(client, monkeypatch):
    monkeypatch.setenv("APP_PASSWORD", "")
    assert client.get("/history").status_code == 200


def test_state_changing_routes_need_fetch_header(client):
    auth = basic("pw-test")
    assert client.post("/delete", headers=auth).status_code == 403
    assert client.post("/delete", headers={**auth, **FETCH}).status_code == 200
    assert client.post("/voice_chat", headers=auth).status_code == 403


def test_delete_is_post_only(client):
    assert client.get("/delete", headers={**basic("pw-test"), **FETCH}).status_code == 405


@pytest.mark.parametrize("sid", ["../../etc/passwd", "1_ABCDEF", "abc", "1_abcdef/../x", ""])
def test_listen_rejects_bad_session_ids(client, sid):
    r = client.get("/listen", query_string={"session_id": sid}, headers=basic("pw-test"))
    assert r.status_code == 400


def test_listen_accepts_issued_format(client):
    r = client.get("/listen?session_id=1700000000_abcdef", headers=basic("pw-test"))
    assert r.status_code == 404  # valid format, file does not exist


def test_save_log_uses_parameters(monkeypatch):
    calls = []

    class FakeClient:
        def query(self, sql, job_config=None):
            calls.append((sql, job_config))
            return "job"

    monkeypatch.setattr(model_chat_log.bigquery, "Client", FakeClient)
    evil = "x''') ; DELETE FROM app.chat_log WHERE TRUE; --"
    model_chat_log.save_log("user", evil)
    sql, cfg = calls[0]
    assert evil not in sql
    assert {p.name: p.value for p in cfg.query_parameters} == {"message": evil, "role": "user"}


def test_listen_ignores_unknown_voice(client, monkeypatch, tmp_path):
    used = []
    monkeypatch.setattr(main, "transcribe", lambda path: "hello")
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda text, voice: used.append(voice) or iter([b"x"]))
    sid = "1700000000_abcdef"
    open(f"/tmp/{sid}_recorded_audio.mp3", "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}&voice=../../evil", headers=basic("pw-test"))
    r.get_data()
    assert r.status_code == 200 and used == ["nova"]


def test_listen_passes_selected_voice(client, monkeypatch):
    used = []
    monkeypatch.setattr(main, "transcribe", lambda path: "hello")
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda text, voice: used.append(voice) or iter([b"x"]))
    sid = "1700000000_abcdee"
    open(f"/tmp/{sid}_recorded_audio.mp3", "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}&voice=onyx", headers=basic("pw-test"))
    r.get_data()
    assert used == ["onyx"]


def test_listen_returns_400_for_too_short_audio(client, monkeypatch):
    from openai import BadRequestError

    def too_short(path):
        # Build the SDK error without an HTTP response object (its constructor
        # signature differs between openai versions).
        err = BadRequestError.__new__(BadRequestError)
        Exception.__init__(err, "Audio file is too short. Minimum audio length is 0.1 seconds.")
        raise err

    streamed = []
    monkeypatch.setattr(main, "transcribe", too_short)
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda text, voice: streamed.append(text) or iter([b"x"]))
    sid = "1700000000_abcded"
    path = f"/tmp/{sid}_recorded_audio.mp3"
    open(path, "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}", headers=basic("pw-test"))
    assert r.status_code == 400
    assert r.get_json()["status"] == "error"
    assert streamed == []
    assert not os.path.exists(path)


def test_listen_streams_transcribed_text(client, monkeypatch):
    seen = []
    monkeypatch.setattr(main, "transcribe", lambda path: "konnichiwa")
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda text, voice: seen.append(text) or iter([b"x"]))
    sid = "1700000000_abcdec"
    open(f"/tmp/{sid}_recorded_audio.mp3", "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}", headers=basic("pw-test"))
    assert r.get_data() == b"x" and seen == ["konnichiwa"]


def test_tts_model_matches_voice():
    assert main.TTS1_VOICES <= main.TTS_VOICES
    for v in ["nova", "alloy", "coral", "onyx", "shimmer"]:
        assert main.tts_model(v) == "tts-1"
    for v in ["ballad", "cedar", "marin", "verse"]:
        assert main.tts_model(v) == "gpt-4o-mini-tts"


def test_stream_uses_model_for_selected_voice(monkeypatch):
    calls = []

    class Delta:
        content = "hello."

    class Choice:
        delta = Delta()

    class Chunk:
        choices = [Choice()]

    class Audio:
        def iter_bytes(self, chunk_size=4096):
            return iter([b"mp3"])

    monkeypatch.setattr(main.client.chat.completions, "create", lambda **kw: iter([Chunk()]))
    monkeypatch.setattr(main.client.audio.speech, "create", lambda **kw: calls.append((kw["model"], kw["voice"])) or Audio())
    monkeypatch.setattr(model_chat_log, "get_logs", lambda: [])
    monkeypatch.setattr(model_chat_log, "save_log", lambda role, text: None)
    assert list(main.openai_voice_to_voice_stream("hi", "marin")) == [b"mp3"]
    assert list(main.openai_voice_to_voice_stream("hi", "nova")) == [b"mp3"]
    assert calls == [("gpt-4o-mini-tts", "marin"), ("tts-1", "nova")]
