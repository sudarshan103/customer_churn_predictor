# Churn Predictor FastAPI Backend

Production-ready FastAPI service that accepts multiple customer sales prompts, calls a fine-tuned OpenAI model asynchronously, and returns structured churn JSON.

## Architecture

- `app/routes.py`: API routes (`/health`, `/predict-churn`), request-id middleware, and rate limiting middleware.
- `app/service.py`: Async OpenAI client integration, concurrent batch processing via `asyncio.gather()`, and model output parsing.
- `app/schemas.py`: Pydantic request/response schemas.
- `app/config.py`: Environment-driven settings via `python-dotenv`.
- Nginx reverse proxy (`nginx/nginx.conf`) in front of Gunicorn + Uvicorn workers.

## Environment & Secrets

### Safe Secret Management

**Use `.env` file (Git-ignored):**

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual API keys in `.env`:
   ```bash
   OPENAI_API_KEY=sk-...
   OPENAI_FINE_TUNED_MODEL=ft:gpt-3.5-turbo:your-model-id
   WORKERS=4
   OPENAI_TIMEOUT_SECONDS=60
   OPENAI_TEMPERATURE=0.7
   OPENAI_MAX_TOKENS=200
   RATE_LIMIT_PER_MINUTE=120
   ```

3. **`.env` is Git-ignored** — your keys will never be committed to the repository.

4. **`.env.example` is committed** — it documents the required variables for other developers (without secrets).

### Required Variables

- `OPENAI_API_KEY` — Your OpenAI API key (keep secret)
- `OPENAI_FINE_TUNED_MODEL` — Your fine-tuned model ID (example: `ft:gpt-3.5-turbo:your-model-id`)
- `WORKERS` — Number of Uvicorn workers (default `4`)
- `OPENAI_TIMEOUT_SECONDS` — OpenAI API timeout (default `60`)
- `OPENAI_TEMPERATURE` — Sampling temperature for predictions, range `0..2` (default `0.7`)
- `OPENAI_MAX_TOKENS` — Max completion tokens per prediction, integer `> 0` (default `200`)
- `RATE_LIMIT_PER_MINUTE` — Request rate limit (default `120`)

## Run Locally (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 10003 --reload
```

## Run with Gunicorn + Uvicorn

```bash
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers ${WORKERS:-4} \
  --bind 0.0.0.0:10003
```

## Docker Build

```bash
docker build -t churn-api:latest .
```

## Docker Compose (App + Nginx)

```bash
docker compose up --build
```

API is available through Nginx at `http://localhost:10003`.

## Endpoints

### Health

`GET /health`

Response:

```json
{"status": "ok"}
```

### Predict Churn

`POST /predict-churn`

Request:

```json
{
  "prompts": [
    "Customer bought 500ml regularly for 6 months...",
    "Customer bought 250ml irregularly for 2 months..."
  ]
}
```

Note: The API is batch-first and always processes a `prompts` list. If you send a single string in `prompts`, it is automatically normalized to a one-item list.

Single customer example:

```json
{
  "prompts": [
    "Customer bought 500ml regularly for 6 months. Price increased by 8%. Last purchase was 18 days ago. Predict churn risk."
  ]
}
```

Many customers example:

```json
{
  "prompts": [
    "Customer bought 500ml regularly for 6 months...",
    "Customer bought 250ml irregularly for 2 months...",
    "Customer bought 1000ml regularly for 4 months..."
  ]
}
```

Response:

```json
{
  "results": [
    {
      "churn_score": 3,
      "reasoning": "High churn risk due to inactivity...",
      "action": "Immediate outreach from support..."
    }
  ]
}
```

## Example cURL

```bash
curl -X POST http://localhost:10003/predict-churn \
  -H "Content-Type: application/json" \
  -d '{
    "prompts": [
      "Customer bought 500ml regularly for 6 months...",
      "Customer bought 250ml irregularly for 2 months..."
    ]
  }'
```

## Notes

- Batch requests are processed concurrently with `asyncio.gather()`.
- Responses are parsed safely into strict typed schema (`churn_score`, `reasoning`, `action`).
- Structured logging includes request count and model latency.
- Includes request ID middleware and simple in-memory rate limiting.
