# GiveThemGist Flask backend

## Routes
- `/` — serves the existing homepage.
- `/login` — server-side admin login.
- `/dashboard` — protected dashboard placeholder.
- `/logout` — POST logout.
- `/api/health` — health endpoint.
- Unknown paths — branded 404.

## Run locally (Windows PowerShell)
```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:FLASK_SECRET_KEY = "replace-with-a-long-random-secret"
$env:ADMIN_USERNAME = "mayowausername"
$env:ADMIN_PASSWORD = "123456789"
$env:COOKIE_SECURE = "false"
python -m flask --app app run --debug
```
Then visit http://127.0.0.1:5000/login. Login: `mayowausername` · Password: `123456789`. Change this demo password before deploying publicly.

## Deploy
Set `FLASK_SECRET_KEY`, `ADMIN_USERNAME`, and `ADMIN_PASSWORD` in your hosting environment variables. For HTTPS production set `COOKIE_SECURE=true`.

## Important
This adds a Flask backend and a protected starter dashboard. The current frontend admin controls are not yet connected to Flask authentication, and the dashboard is a placeholder. This starter uses environment credentials; use a proper database/user-management flow before expanding to multiple administrators. Do not store persistent uploads or database files on Vercel's ephemeral filesystem.
