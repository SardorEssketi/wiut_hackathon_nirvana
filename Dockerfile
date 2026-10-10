FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
ARG TORCH_VERSION=2.14.1
ARG MODEL_REVISION=614241f622f53c4eeff9890bdc4f31cfecc418b3
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 POLISDIFF_MODEL_PATH=/app/models/multilingual-e5-small \
    HF_HUB_DISABLE_TELEMETRY=1 POLISDIFF_TORCH_THREADS=2
# CPU wheel avoids downloading CUDA libraries on CPU-only demo hosts.
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==${TORCH_VERSION}
COPY requirements.runtime.lock.txt ./
RUN pip install --no-cache-dir -r requirements.runtime.lock.txt
COPY scripts/download_model.py scripts/download_model.py
ENV POLISDIFF_MODEL_REVISION=${MODEL_REVISION}
RUN python scripts/download_model.py
COPY . .
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
USER appuser
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8501')+'/_stcore/health',timeout=4)"
CMD ["python", "main.py"]
