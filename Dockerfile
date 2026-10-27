FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN python -m pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATABASE=/app/instance/aurora.db
WORKDIR /app
RUN groupadd --system --gid 10001 appuser \
    && useradd --system --uid 10001 --gid appuser \
       --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/instance \
    && chown -R appuser:appuser /app
COPY --from=builder /install/ /usr/local/
COPY --chown=appuser:appuser app/ /app/app/
USER appuser
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"]
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:create_app()"]
