# Workout Logger API

A small REST API for logging and reviewing workouts, built with Python and Flask, backed by SQLite. Protected with API key authentication, covered by an automated test suite, containerised with Docker, and deployed live on Render. Integrated with an [n8n](https://n8n.io) automation workflow that calls it on a schedule, demonstrating how a custom backend can be plugged into a no-code automation tool.

**Live API:** https://workout-logger-api-nfx7.onrender.com

> Note: this is deployed on Render's free tier, which spins the service down after ~15 minutes of inactivity. The first request after idle time may take 30–60 seconds to respond while it wakes back up — this is expected, not a bug.

## What it does

- Log a workout (exercise, duration, date, notes)
- View all logged workouts, with an optional filter by exercise name
- Delete a workout by ID
- View a summary report (times performed and total minutes per exercise)
- Write operations (logging and deleting) are protected by an API key
- Automatically triggered on a schedule via an n8n workflow, which calls the API's `/workouts` endpoint

## Endpoints

| Method | Endpoint                    | Auth required | Description                                                  |
| ------ | ---------------------------- | :------------: | ------------------------------------------------------------ |
| GET    | `/`                          | No             | Health check — confirms the API is running                   |
| POST   | `/workouts`                  | **Yes**        | Log a new workout                                             |
| GET    | `/workouts`                  | No             | List all workouts (newest first)                              |
| GET    | `/workouts?exercise=Squats`  | No             | List workouts filtered by exercise name                       |
| DELETE | `/workouts/<id>`             | **Yes**        | Delete a workout by its ID                                    |
| GET    | `/workouts/summary`          | No             | Aggregate report — times done and total minutes per exercise  |

All input is validated: missing or invalid fields return a `400` error with a clear message, and deleting a non-existent workout returns a `404`.

## Authentication

`POST /workouts` and `DELETE /workouts/<id>` require an API key, passed as a header:

```
X-API-Key: your-key-here
```

Requests to these endpoints without a valid key return `401 Unauthorized`. Read-only endpoints (`GET`) are open.

## Database schema

A single `Workouts` table in SQLite:

- `id` — auto-incrementing primary key
- `exercise` — text, required
- `duration_minutes` — number, optional
- `date` — text (defaults to today if not provided)
- `notes` — text, optional

## Testing

The project has a `pytest` suite covering successful and failing cases for every endpoint (validation errors, missing/invalid API keys, filtering, aggregation, deletes of non-existent records) — 15 tests in total, run against a temporary, isolated SQLite database so nothing touches real data.

```bash
pip install -r requirements.txt
pytest -v
```

Tests run automatically on every push via GitHub Actions — see the Actions tab for current status.

## n8n automation

A scheduled n8n workflow (`n8n-workflow.json`) runs daily and sends an authenticated POST request to this API's `/workouts` endpoint to log an entry automatically. See the workflow diagram below.

[![n8n workflow](https://github.com/danielibikunle2/workout-logger-api/raw/main/N8N.png)](/danielibikunle2/workout-logger-api/blob/main/N8N.png)

## Tech stack

- Python 3, Flask
- SQLite (via Python's built-in `sqlite3` module)
- pytest (automated testing)
- GitHub Actions (CI)
- Docker (containerisation)
- Render (deployment)
- n8n (workflow automation)

## Local setup

1. Clone the repository and move into it:

   ```bash
   git clone https://github.com/danielibikunle2/workout-logger-api.git
   cd workout-logger-api
   ```

2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Create the database:

   ```bash
   python3 create_db.py
   ```

5. (Optional but recommended) Set an API key so write endpoints are protected locally too:

   ```bash
   export API_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
   ```

   If `API_KEY` isn't set, write endpoints stay open for convenience during local testing — a warning is printed on startup as a reminder.

6. Run the API:

   ```bash
   python3 app.py
   ```

   The API will be available at `http://127.0.0.1:5001`.

## Running with Docker

```bash
docker build -t workout-logger-api .
docker run -p 5001:5001 -e API_KEY="your-key-here" workout-logger-api
```

## Example requests

```bash
curl -X POST http://127.0.0.1:5001/workouts \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key-here" \
  -d '{"exercise": "Squats", "duration_minutes": 30, "notes": "Leg day"}'

curl http://127.0.0.1:5001/workouts

curl http://127.0.0.1:5001/workouts/summary
```

## Deployment

Deployed on [Render](https://render.com) as a web service:

- **Build command:** `pip install -r requirements.txt && python create_db.py`
- **Start command:** `python app.py`
- **Environment variable:** `API_KEY` set to a long random secret

## Possible future improvements

- Add a PUT endpoint to edit existing workout entries
- Move from a single shared API key to per-user accounts with JWT auth
- Persist the database somewhere durable (Render's free tier filesystem is ephemeral, so data can be lost on redeploy) — e.g. a managed Postgres instance
- Trigger the n8n workflow from a Telegram or webhook message instead of only a schedule

## About

Built as a personal project to practice REST API design, testing, and deployment end to end.