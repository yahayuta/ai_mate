import base64

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
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda path, voice: used.append(voice) or iter([b"x"]))
    sid = "1700000000_abcdef"
    open(f"/tmp/{sid}_recorded_audio.mp3", "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}&voice=../../evil", headers=basic("pw-test"))
    r.get_data()
    assert r.status_code == 200 and used == ["nova"]


def test_listen_passes_selected_voice(client, monkeypatch):
    used = []
    monkeypatch.setattr(main, "openai_voice_to_voice_stream", lambda path, voice: used.append(voice) or iter([b"x"]))
    sid = "1700000000_abcdee"
    open(f"/tmp/{sid}_recorded_audio.mp3", "wb").write(b"a")
    r = client.get(f"/listen?session_id={sid}&voice=onyx", headers=basic("pw-test"))
    r.get_data()
    assert used == ["onyx"]
