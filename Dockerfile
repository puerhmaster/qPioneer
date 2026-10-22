# qPioneer: docker build -t qpioneer . && docker run --rm -p 127.0.0.1:8501:8501 qpioneer
# Ключи облачного сохранения (по желанию): смонтируйте secrets.toml в /app/.streamlit/secrets.toml (см. README).
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY .streamlit/config.toml .streamlit/config.toml
COPY qpcr_analyse_app.py ./
COPY examples ./examples
COPY fonts ./fonts

USER app
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8501/_stcore/health', timeout=4)"
CMD ["streamlit", "run", "qpcr_analyse_app.py"]
