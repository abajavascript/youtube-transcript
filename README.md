# YouTube Transcript

Fetch **metadata and transcripts** for public YouTube videos using [`yt-transcript.py`](yt-transcript.py), and optionally expose the same logic over HTTP via a small **FastAPI** app ([`app.py`](app.py)) for local use or [Vercel](https://vercel.com/) deployment.

Transcripts are resolved through **yt-dlp** (metadata and captions when available) and **youtube-transcript-api**, with fallbacks described in the implementation. **Single watch-style URLs only** (including `youtu.be`, `/watch?v=`, `/shorts/`, `/embed/`); playlists are not supported as input.

## Requirements

- **Python 3.10+** (tested in development on newer 3.x releases)
- Dependencies listed in [`requirements.txt`](requirements.txt)

## Project layout

| File | Purpose |
|------|---------|
| `yt-transcript.py` | CLI: one or more URLs → JSON on stdout |
| `app.py` | FastAPI ASGI app: health + `/api/transcript` |
| `requirements.txt` | Python dependencies (includes `uvicorn` for local serving) |
| `vercel.json` | Vercel function settings (`maxDuration`, file excludes) |

## Local setup

From the repository root:

```powershell
python -m pip install -r requirements.txt
```

## Test the CLI (`yt-transcript.py`)

```powershell
python yt-transcript.py "https://www.youtube.com/watch?v=jNQXAC9IVRw"
```

Expect pretty-printed JSON with a top-level `videos` array (title, transcript text, `failure_reason` when applicable, etc.). Pass multiple URLs as separate arguments to process them in one run.

## Run the API locally (`app.py`)

Start the ASGI server with Uvicorn:

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8000
```

Then open in a browser:

- [http://127.0.0.1:8000/](http://127.0.0.1:8000/) — health check (`{"status":"ok"}`)
- [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) — interactive OpenAPI (Swagger UI)

### API usage

- **GET** `/api/transcript?url=<encoded-youtube-url>`
- **POST** `/api/transcript` with JSON body: `{"url": "<youtube-url>"}`

Response shape matches the CLI: `{"videos": [<result object>]}`.

### Optional API token

If the environment variable **`TRANSCRIPT_API_TOKEN`** is set, every `/api/transcript` request must include:

```http
Authorization: Bearer <same value as TRANSCRIPT_API_TOKEN>
```

If it is unset, the transcript routes are open (no auth header required).

### Port already in use (Windows)

If Uvicorn fails with an error like **WinError 10013** or “address already in use”, another process may be bound to that port. Check with `netstat -ano | findstr ":8000"` and stop that PID, or run on a free port, for example:

```powershell
python -m uvicorn app:app --reload --host 127.0.0.1 --port 8010
```

## Deploy to Vercel

1. **Repository** — Push this project to GitHub, GitLab, or Bitbucket (or connect a local directory with the Vercel CLI).
2. **New project** — In the [Vercel dashboard](https://vercel.com/dashboard), import the repository as a new project.
3. **Runtime** — Vercel will detect Python from `requirements.txt` and use [`vercel.json`](vercel.json) for function configuration (for example **`maxDuration`: 60** seconds for `app.py`). Increase `maxDuration` in `vercel.json` if transcript fetches time out, within your plan’s limits.
4. **Environment variables** (optional) — In the project **Settings → Environment Variables**, add `TRANSCRIPT_API_TOKEN` if you want bearer-token protection on `/api/transcript`.
5. **Deploy** — Trigger a deployment; production URL will be shown in the dashboard.

After deploy, use your production origin the same way as locally, for example `https://<your-project>.vercel.app/docs` for Swagger, or call `/api/transcript` with your production base URL.

### Vercel CLI (optional)

With [Vercel CLI](https://vercel.com/docs/cli) installed and logged in:

```powershell
vercel
```

Follow prompts to link the folder and deploy previews or production.

## License

Add a `LICENSE` file if you intend to open-source this repository; none is included by default in this layout.
