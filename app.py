import hmac
import os
import secrets
from datetime import timedelta
from functools import wraps
from pathlib import Path

from flask import Flask, abort, redirect, render_template_string, request, session, url_for, send_from_directory

ROOT = Path(__file__).resolve().parent
app = Flask(__name__, static_folder="static", static_url_path="/static")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "")
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "true").lower() == "true",
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "mayowausername")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "123456789")

LOGIN_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Admin Login | GiveThemGist</title>
<style>
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;padding:20px;background:#090909;color:#f7f7f7;font:16px system-ui,sans-serif}
main{width:min(100%,420px);padding:32px;background:#151515;border:1px solid #303030;border-radius:14px}
h1{margin:0 0 8px;font-size:30px}p{color:#aaa;line-height:1.6}label{display:block;margin:18px 0 8px;font-size:14px}
input{width:100%;padding:13px;background:#090909;color:white;border:1px solid #444;border-radius:8px}
button{width:100%;padding:14px;margin-top:22px;background:#e21d2f;color:white;border:0;border-radius:8px;font-weight:700;cursor:pointer}
.error{color:#ff8d8d}.back{display:block;margin-top:20px;text-align:center;color:#aaa}
</style></head><body><main><h1>Admin login</h1><p>Sign in to access the administration area.</p>
{% if error %}<p class="error" role="alert">{{ error }}</p>{% endif %}
<form method="post" action="/login">
<input type="hidden" name="csrf_token" value="{{ csrf_token }}">
<label for="username">Username</label><input id="username" name="username" autocomplete="username" required>
<label for="password">Password</label><input id="password" name="password" type="password" autocomplete="current-password" required>
<button type="submit">Sign in</button></form><a class="back" href="/">← Back to website</a></main></body></html>"""

DASHBOARD_PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Admin Dashboard | GiveThemGist</title><style>
body{margin:0;padding:32px;background:#090909;color:#f5f5f5;font:16px system-ui;max-width:900px;margin:auto}
main{padding:28px;background:#151515;border:1px solid #303030;border-radius:14px}
a{color:#ff5260}button{padding:10px 16px;background:#e21d2f;color:#fff;border:0;border-radius:6px;cursor:pointer}
</style></head><body><main><h1>Admin dashboard</h1>
<p>Authentication is active. This is a protected starter dashboard; your existing admin interface still needs to be connected here.</p>
<form method="post" action="/logout"><button type="submit">Log out</button></form>
<p><a href="/">View website</a></p></main></body></html>"""

def check_auth_config():
    if not app.secret_key or not ADMIN_USERNAME or not ADMIN_PASSWORD:
        abort(503, description="Authentication is not configured. Set FLASK_SECRET_KEY, ADMIN_USERNAME, and ADMIN_PASSWORD in your environment.")

def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("is_admin"):
            return redirect(url_for("login", next=request.path))
        return view(*args, **kwargs)
    return wrapped

@app.get("/")
def home():
    return send_from_directory(ROOT / "static", "index.html")

@app.get("/<path:filename>")
def frontend_file(filename):
    # Serve the other existing project HTML pages and static assets safely.
    if filename in ("givethemgist.html", "kilburn-shop.html"):
        return send_from_directory(ROOT / "static", filename)
    abort(404)

@app.route("/login", methods=["GET", "POST"])
def login():
    check_auth_config()
    error = None
    if request.method == "POST":
        submitted_token = request.form.get("csrf_token", "")
        if not hmac.compare_digest(submitted_token, session.get("csrf_token", "")):
            error = "Session expired. Refresh the page and try again."
        else:
            username = request.form.get("username", "")
            password = request.form.get("password", "")
            user_ok = hmac.compare_digest(username, ADMIN_USERNAME)
            pass_ok = hmac.compare_digest(password, ADMIN_PASSWORD)
            if user_ok and pass_ok:
                session.clear()
                session["is_admin"] = True
                session.permanent = True
                target = request.args.get("next", "")
                if not target.startswith("/") or target.startswith("//"):
                    target = url_for("dashboard")
                return redirect(target)
            error = "Invalid username or password."
    session["csrf_token"] = secrets.token_urlsafe(32)
    return render_template_string(LOGIN_PAGE, error=error, csrf_token=session["csrf_token"])

@app.get("/dashboard")
@admin_required
def dashboard():
    return render_template_string(DASHBOARD_PAGE)

@app.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.get("/api/health")
def health():
    return {"status": "ok", "app": "GiveThemGist"}

@app.errorhandler(404)
def page_not_found(_error):
    return render_template_string("""<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>404 — Page not found</title><style>body{margin:0;min-height:100vh;display:grid;place-items:center;background:#090909;color:#fff;font:16px system-ui;text-align:center;padding:20px}
.code{font-size:clamp(80px,18vw,150px);font-weight:900;color:#e21d2f;line-height:1}a{color:#ff5260}</style>
<main><div class="code">404</div><h1>Page not found</h1><p>This page may have moved or no longer exists.</p><a href="/">Back to home</a></main></html>"""), 404
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)