import logging
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.schemas import ChurnRequest, ChurnResponse
from app.service import ChurnPredictionService, InMemoryRateLimiter, ModelResponseParseError

logger = logging.getLogger(__name__)

router = APIRouter()


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith("/predict-churn"):
            rate_limiter: InMemoryRateLimiter = request.app.state.rate_limiter
            allowed = await rate_limiter.allow()
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={"detail": "Rate limit exceeded"},
                )
        return await call_next(request)


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def service_dependency(request: Request) -> ChurnPredictionService:
    return request.app.state.churn_service


@router.post("/predict-churn", response_model=ChurnResponse)
async def predict_churn(
    payload: ChurnRequest,
    request: Request,
    service: ChurnPredictionService = Depends(service_dependency),
) -> ChurnResponse:
    request_count = len(payload.prompts)
    logger.info(
        "Received predict request",
        extra={"request_id": request.state.request_id, "prompt_count": request_count},
    )

    started = time.perf_counter()
    try:
        results, model_latency_ms = await service.predict_many(payload.prompts)
    except TimeoutError as exc:
        raise HTTPException(status_code=status.HTTP_504_GATEWAY_TIMEOUT, detail=str(exc)) from exc
    except ModelResponseParseError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error") from exc

    total_latency_ms = (time.perf_counter() - started) * 1000
    logger.info(
        "Completed predict request",
        extra={
            "request_id": request.state.request_id,
            "prompt_count": request_count,
            "model_latency_ms": round(model_latency_ms, 2),
            "total_latency_ms": round(total_latency_ms, 2),
        },
    )
    return ChurnResponse(results=results)
