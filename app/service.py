import asyncio
import logging
import re
import time
from collections import deque
from dataclasses import dataclass
from typing import Final

from openai import AsyncOpenAI

from app.config import get_settings
from app.schemas import ChurnResult

logger = logging.getLogger(__name__)

SCORE_PATTERN: Final[re.Pattern[str]] = re.compile(r"Churn\s*Score\s*:\s*(\d+)", re.IGNORECASE)
REASONING_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"Reasoning\s*:\s*(.*?)(?:\n\s*Action\s*:|$)",
    re.IGNORECASE | re.DOTALL,
)
ACTION_PATTERN: Final[re.Pattern[str]] = re.compile(r"Action\s*:\s*(.*)$", re.IGNORECASE | re.DOTALL)


class ModelResponseParseError(ValueError):
    pass


@dataclass
class InMemoryRateLimiter:
    max_requests: int
    window_seconds: int = 60

    def __post_init__(self) -> None:
        self._events: deque[float] = deque()
        self._lock = asyncio.Lock()

    async def allow(self) -> bool:
        now = time.monotonic()
        async with self._lock:
            while self._events and now - self._events[0] > self.window_seconds:
                self._events.popleft()
            if len(self._events) >= self.max_requests:
                return False
            self._events.append(now)
            return True


class ChurnPredictionService:
    def __init__(self) -> None:
        settings = get_settings()
        self._model = settings.openai_fine_tuned_model
        self._timeout = settings.openai_timeout_seconds
        self._temperature = settings.openai_temperature
        self._max_tokens = settings.openai_max_tokens
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def predict_many(self, prompts: list[str]) -> tuple[list[ChurnResult], float]:
        start = time.perf_counter()
        tasks = [self._predict_one(prompt) for prompt in prompts]
        results = await asyncio.gather(*tasks)
        latency_ms = (time.perf_counter() - start) * 1000
        return results, latency_ms

    async def _predict_one(self, prompt: str) -> ChurnResult:
        if not self._model:
            raise RuntimeError("OPENAI_FINE_TUNED_MODEL is not configured")

        try:
            completion = await asyncio.wait_for(
                self._client.chat.completions.create(
                    model=self._model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self._temperature,
                    max_tokens=self._max_tokens,
                ),
                timeout=self._timeout,
            )
        except asyncio.TimeoutError as exc:
            raise TimeoutError("Timed out waiting for OpenAI response") from exc

        content = (completion.choices[0].message.content or "").strip()
        return self._parse_response(content)

    @staticmethod
    def _parse_response(text: str) -> ChurnResult:
        score_match = SCORE_PATTERN.search(text)
        reasoning_match = REASONING_PATTERN.search(text)
        action_match = ACTION_PATTERN.search(text)

        if not score_match or not reasoning_match or not action_match:
            raise ModelResponseParseError("Malformed model response")

        try:
            score = int(score_match.group(1))
        except ValueError as exc:
            raise ModelResponseParseError("Invalid churn score format") from exc

        reasoning = reasoning_match.group(1).strip()
        action = action_match.group(1).strip()

        return ChurnResult(churn_score=score, reasoning=reasoning, action=action)
