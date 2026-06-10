FROM python:3.11-slim

WORKDIR /app

COPY app_api/requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY app_api/src /app/src

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["tail", "-f", "/dev/null"]