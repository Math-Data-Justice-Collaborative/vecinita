from pydantic import BaseModel, ConfigDict


class EmbedRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"text": "Community clinic walk-in triage policy", "model_version": None},
                {"text": "SNAP interview documents checklist", "model_version": "v1"},
                {"text": "Housing lottery preference categories", "model_version": None},
                {"text": "Transit reduced fare eligibility", "model_version": "v2"},
                {"text": "Cooling center map legend", "model_version": "v1"},
            ]
        }
    )

    text: str
    model_version: str | None = None


class EmbedResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"embedding": [0.1, -0.1, 0.2], "model_version": None},
                {"embedding": [0.0, 0.01], "model_version": "v1"},
                {"embedding": [-0.5, 0.0, 0.5], "model_version": "v2"},
                {"embedding": [0.02, 0.02], "model_version": None},
                {"embedding": [1.0, 0.0], "model_version": "v1"},
            ]
        }
    )

    embedding: list[float]
    model_version: str | None = None
