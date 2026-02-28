# Customer Churn Predictor API

FastAPI service for predicting customer churn risk using a fine-tuned GPT-3.5 Turbo model. Returns structured predictions with churn scores (1-3), reasoning, and recommended actions.

## Quick Start

```bash
# 1. Clone and setup environment
cp .env.example .env
# Edit .env with your OpenAI API key and fine-tuned model ID

# 2. Install dependencies
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 3. Run the service
uvicorn app.main:app --host 0.0.0.0 --port 10003
```

Service will be available at `http://localhost:10003`

## Project Structure

```
├── app/                      # FastAPI application
│   ├── main.py              # App entry point
│   ├── routes.py            # API endpoints
│   ├── service.py           # OpenAI integration
│   ├── schemas.py           # Pydantic models
│   └── config.py            # Configuration
├── notebooks/               # Jupyter notebooks
│   ├── train_model.ipynb    # Fine-tuning notebook
│   ├── inference.ipynb      # Prediction notebook
│   └── train_gpt35_turbo.ipynb  # Original training notebook (reference)
├── generate_customer_churn.py  # Training data generator
└── docker-compose.yml       # Docker setup
```

## Notebooks

All notebooks are located in the `notebooks/` folder.

### Fine-tuning: `train_model.ipynb`

Train a GPT-3.5 Turbo model on customer churn data:
- Upload training data to OpenAI
- Create and monitor fine-tuning jobs
- View training metrics and costs
- List all fine-tuning jobs

**Prerequisites:**
- Set `OPEN_AI_FINE_TUNING_KEY` environment variable
- Training data: `churn_dataset_gpt35_turbo.jsonl`

### Inference: `inference.ipynb`

Use the fine-tuned model for predictions:
- Single customer predictions
- Batch predictions
- Model comparison (base vs fine-tuned)
- Export predictions to JSON

**Prerequisites:**
- Set `CUSTOMER_CHURN_OPEN_AI_MODEL` environment variable

## Configuration

Create a `.env` file with the following variables:

```bash
OPENAI_API_KEY=sk-...
OPENAI_FINE_TUNED_MODEL=ft:gpt-3.5-turbo:your-model-id
OPENAI_TIMEOUT_SECONDS=60
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=200
WORKERS=4
RATE_LIMIT_PER_MINUTE=120
```

## Deployment

### Local Development

```bash
uvicorn app.main:app --host 0.0.0.0 --port 10003 --reload
```

### Production with Gunicorn

```bash
gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  --workers 4 \
  --bind 0.0.0.0:10003
```

### Docker Compose

```bash
docker compose up --build
```

Access via Nginx at `http://localhost:10003`

## API Reference

### Health Check

**GET** `/health`

```json
{"status": "ok"}
```

### Predict Customer Churn

**POST** `/predict-churn`

**Request:**
```json
{
  "prompts": [
    "Customer bought 500ml regularly for 6 months. Price increased by 8% recently. Last purchase was 18 days ago. Predict churn risk.",
    "Customer bought 250ml irregularly for 2 months. Price increased by 15% recently. They raised 2 complaint(s) about product defect. Last purchase was 40 days ago. Predict churn risk."
  ]
}
```

**Response:**
```json
{
  "results": [
    {
      "churn_score": 2,
      "reasoning": "Moderate churn risk due to noticeable price increase or minor service issues.",
      "action": "Offer moderate loyalty credits or targeted discounts to prevent churn."
    },
    {
      "churn_score": 3,
      "reasoning": "High churn risk due to inactivity, major complaints, and strong competitor offers.",
      "action": "Immediate outreach from support with personalized discount or offer."
    }
  ]
}
```

**Churn Score:**
- `1` - Low risk (stable customer)
- `2` - Moderate risk (requires attention)
- `3` - High risk (immediate action needed)

## Features

- **Batch Processing**: Process multiple customer profiles concurrently
- **Rate Limiting**: Built-in rate limiting (120 requests/minute)
- **Request Tracking**: Request ID middleware for tracing
- **Structured Output**: Validated responses with churn score, reasoning, and actionable recommendations
- **Production Ready**: Gunicorn + Uvicorn workers with Nginx reverse proxy support

## Architecture

- **Routes** (`app/routes.py`): API endpoints, middleware, rate limiting
- **Service** (`app/service.py`): OpenAI integration, async batch processing
- **Schemas** (`app/schemas.py`): Pydantic models for request/response validation
- **Config** (`app/config.py`): Environment-based configuration
