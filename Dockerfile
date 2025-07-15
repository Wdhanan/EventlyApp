# Multi-Stage Build für optimierte Image-Größe
FROM python:3.9-slim as builder

WORKDIR /app
COPY requirements.txt .

# Installiere Build-Abhängigkeiten
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc python3-dev && \
    pip install --user -r requirements.txt && \
    apt-get remove -y gcc python3-dev && \
    apt-get autoremove -y

# Finales Image
FROM python:3.9-slim

WORKDIR /app

# Kopiere nur notwendige Dateien
COPY --from=builder /root/.local /root/.local
COPY . .

# Datenbank-Verzeichnis erstellen
RUN mkdir -p /app/data && \
    chmod a+rwx /app/data

# Umgebungsvariablen
ENV PATH=/root/.local/bin:$PATH \
    STREAMLIT_SERVER_PORT=8501 \
    PYTHONPATH=/app \
    STREAMLIT_SERVER_HEADLESS=true

# Port freigeben
EXPOSE 8501

# Gesundheitscheck
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Nicht als root laufen
RUN useradd -m appuser && chown -R appuser /app
USER appuser

# Startbefehl
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]