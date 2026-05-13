from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ScrapeRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"url": "https://example.org/resources", "depth": 1},
                {"url": "https://city.gov/housing", "depth": 2},
                {"url": "https://health.example/clinics", "depth": 1},
                {"url": "https://wiki.example/guide", "depth": 3},
                {"url": "https://schools.example/news", "depth": 1},
            ]
        }
    )

    url: HttpUrl
    depth: int = 1


class ScrapeResult(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "url": "https://example.org/page",
                    "title": "Resource page",
                    "text": "First paragraph of extracted text.",
                    "metadata": {"source": "crawl"},
                },
                {
                    "url": "https://city.gov/housing",
                    "title": None,
                    "text": None,
                    "metadata": {},
                },
                {
                    "url": "https://health.example/wic",
                    "title": "WIC",
                    "text": "Walk-in hours…",
                    "metadata": {"lang": "en"},
                },
                {
                    "url": "https://transit.example/14",
                    "title": "Route 14",
                    "text": "Schedule excerpt",
                    "metadata": {"route": "14"},
                },
                {
                    "url": "https://schools.example/enroll",
                    "title": "Enrollment",
                    "text": "Proof of residency…",
                    "metadata": {"year": 2026},
                },
            ]
        }
    )

    url: str
    title: str | None = None
    text: str | None = None
    metadata: dict = Field(default_factory=dict)
