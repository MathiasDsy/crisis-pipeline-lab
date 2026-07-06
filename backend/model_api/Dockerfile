FROM python:3.11-slim

WORKDIR /app

# Dépendances Python
COPY model_api/requirements.txt .

# CPU-only torch (no CUDA): the models run on CPU, so we skip the ~2.5GB GPU wheel
# that otherwise blows the image up to ~14GB and the build to ~20min.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Code source
COPY model_api/scripts /app/scripts
COPY model_api/src /app/src
COPY model_api/entrypoint.sh /app/entrypoint.sh

# Corrige les fins de ligne Windows (CRLF -> LF) et rend le script exécutable
RUN sed -i 's/\r$//' /app/entrypoint.sh \
 && chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV MODELS_DIR=/app/storage/models

# L'entrypoint télécharge les modèles si besoin puis lance le serveur
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]FROM python:3.11-slim

WORKDIR /app

# Dépendances Python
COPY model_api/requirements.txt .

# CPU-only torch (no CUDA): the models run on CPU, so we skip the ~2.5GB GPU wheel
# that otherwise blows the image up to ~14GB and the build to ~20min.
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir torch==2.12.0 --index-url https://download.pytorch.org/whl/cpu \
 && pip install --no-cache-dir -r requirements.txt

# Code source
COPY model_api/scripts /app/scripts
COPY model_api/src /app/src
COPY model_api/entrypoint.sh /app/entrypoint.sh

# Corrige les fins de ligne Windows (CRLF -> LF) et rend le script exécutable
RUN sed -i 's/\r$//' /app/entrypoint.sh \
 && chmod +x /app/entrypoint.sh

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1
ENV MODELS_DIR=/app/storage/models

# L'entrypoint télécharge les modèles si besoin puis lance le serveur
ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["python", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8001"]