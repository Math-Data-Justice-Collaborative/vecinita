from pydantic import BaseModel, ConfigDict


class PredictRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"text": "Tenant received three-day pay-or-quit notice", "model_version": None},
                {"text": "Applicant asks about WIC income limits", "model_version": "v1"},
                {"text": "Question about bus pass renewal office hours", "model_version": None},
                {"text": "Food bank first visit ID requirements", "model_version": "v2"},
                {"text": "School enrollment proof of residency options", "model_version": None},
            ]
        }
    )

    text: str
    model_version: str | None = None


class PredictResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"label": "housing_intake", "score": 0.92, "model_version": None},
                {"label": "health_screening", "score": 0.71, "model_version": "v1"},
                {"label": "transit_info", "score": 0.55, "model_version": None},
                {"label": "food_assistance", "score": 0.88, "model_version": "v2"},
                {"label": "unknown", "score": 0.1, "model_version": None},
            ]
        }
    )

    label: str
    score: float
    model_version: str | None = None
