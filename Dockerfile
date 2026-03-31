FROM python:3.11-slim AS builder

WORKDIR /build

COPY cifra_app/requirements.txt .

RUN pip install --upgrade pip --no-cache-dir \
 && pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM python:3.11-slim

LABEL maintainer="você" \
      version="1.1" \
      description="Cifra do Centro - FastAPI"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN groupadd --system --gid 1001 cifra \
 && useradd --system --uid 1001 --gid cifra \
            --no-create-home --shell /sbin/nologin cifra

COPY --from=builder /install /usr/local

WORKDIR /app

COPY cifra_app/main.py ./main.py
COPY cifra_app/cifra.py ./cifra.py
COPY cifra_static/ ./static/

RUN chown -R cifra:cifra /app

RUN chmod -R 550 /app \
 && chmod -R 440 /app/static

USER cifra

EXPOSE 8080

CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8080", \
     "--workers", "2"]
