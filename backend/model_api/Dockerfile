FROM python:3.11-slim

WORKDIR /app

COPY model_api/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY model_api/src /app/src

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]