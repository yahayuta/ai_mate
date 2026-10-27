"""Access control for the AI Mate web app.

The app is deployed to Cloud Run with public access, so every request
(including the page and static files) needs HTTP Basic auth with APP_PASSWORD.
If APP_PASSWORD is not set, requests are allowed only when running locally;
on Cloud Run (K_SERVICE is set) they are refused.
"""
import hmac
import os
import re

from flask import Response, request

SESSION_ID_RE = re.compile(r"\d{1,12}_[0-9a-f]{6}")
STATE_CHANGING = {"voice_chat", "delete_log", "run_streamlit"}


def _same(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode("utf-8"), b.encode("utf-8"))


def _unauthorized():
    return Response("Authentication required", 401, {"WWW-Authenticate": 'Basic realm="AI Mate"'})


def check_request():
    """Flask before_request hook. Returns a response to stop the request, or None to continue."""
    password = os.environ.get("APP_PASSWORD", "")
    if not password:
        if os.environ.get("K_SERVICE"):
            print("APP_PASSWORD is not set; refusing requests on Cloud Run")
            return Response("APP_PASSWORD is not configured", 503)
    else:
        auth = request.authorization
        if not auth or not auth.password or not _same(password, auth.password):
            return _unauthorized()

    # Browsers resend Basic credentials on cross-site requests, so require a
    # header that a plain cross-site form cannot set on endpoints that cost money or change data.
    if request.endpoint in STATE_CHANGING and request.headers.get("X-Requested-With") != "fetch":
        return Response("Missing X-Requested-With header", 403)
    return None


def is_valid_session_id(session_id: str | None) -> bool:
    return bool(session_id) and SESSION_ID_RE.fullmatch(session_id) is not None
