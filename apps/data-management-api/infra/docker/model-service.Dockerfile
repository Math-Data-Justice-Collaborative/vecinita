# Local compose image for vecinita-model (replaces removed `apps/backend/model-service` submodule).
# Production uses Modal; the vecinita monorepo also ships `modal-apps/model-modal/Dockerfile`.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl git ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ARG VECINITA_MODEL_REPO=https://github.com/Math-Data-Justice-Collaborative/vecinita-model.git
ARG VECINITA_MODEL_REF=main
RUN git clone --depth 1 --branch "${VECINITA_MODEL_REF}" "${VECINITA_MODEL_REPO}" /tmp/vecinita-model \
    && cp /tmp/vecinita-model/pyproject.toml /tmp/vecinita-model/README.md /app/ \
    && cp -a /tmp/vecinita-model/src /app/src \
    && rm -rf /tmp/vecinita-model

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir . \
    && pip install --no-cache-dir uvicorn

EXPOSE 8000

CMD ["uvicorn", "vecinita.asgi:app", "--host", "0.0.0.0", "--port", "8000"]
