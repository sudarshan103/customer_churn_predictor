import logging

from fastapi import FastAPI

from app.config import get_settings
from app.routes import RequestIDMiddleware, RateLimitMiddleware, router
from app.service import ChurnPredictionService, InMemoryRateLimiter


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


configure_logging()
settings = get_settings()
app = FastAPI(title=settings.app_name, version=settings.app_version)

app.state.churn_service = ChurnPredictionService()
app.state.rate_limiter = InMemoryRateLimiter(max_requests=settings.rate_limit_per_minute)

app.add_middleware(RequestIDMiddleware)
app.add_middleware(RateLimitMiddleware)
app.include_router(router)
