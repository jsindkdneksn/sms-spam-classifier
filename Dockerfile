ARG BASE_IMAGE=python:3.12-slim
FROM ${BASE_IMAGE}
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements-app.txt ./
RUN python -m pip install --no-cache-dir -r requirements-app.txt
ARG MODEL_DIR=models/release
COPY app/ ./app/
COPY ${MODEL_DIR}/ ./models/release/
USER 10001:10001
ENV MODEL_PATH=/app/models/release/model.joblib MODEL_METADATA_PATH=/app/models/release/metadata.json
EXPOSE 8000
HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
