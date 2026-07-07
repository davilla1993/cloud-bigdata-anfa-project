# Dockerfile — Exportateur de fraîcheur Anfa
# ────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY anfa_freshness_exporter.py .

# Port sur lequel l'exportateur expose /metrics
EXPOSE 8000

CMD ["python", "anfa_freshness_exporter.py"]
