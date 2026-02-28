from pydantic import BaseModel, Field, model_validator


class ChurnRequest(BaseModel):
    prompts: list[str] = Field(
        ...,
        min_length=1,
        description="Each prompt represents one customer's sales record.",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_prompts(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data

        prompts = data.get("prompts")
        if isinstance(prompts, str):
            normalized = data.copy()
            normalized["prompts"] = [prompts]
            return normalized

        return data


class ChurnResult(BaseModel):
    churn_score: int = Field(..., ge=1, le=3)
    reasoning: str = Field(..., min_length=1)
    action: str = Field(..., min_length=1)


class ChurnResponse(BaseModel):
    results: list[ChurnResult]
