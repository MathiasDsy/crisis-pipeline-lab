FROM python:3.11-slim

WORKDIR /app

COPY model_api/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY model_api/scripts /app/scripts
COPY model_api/src /app/src
COPY model_api/entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV MODELS_DIR=/app/storage/models

# entrypoint provisions the models, then execs the CMD (or the compose `command`)
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]