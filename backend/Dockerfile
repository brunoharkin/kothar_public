FROM python:3.12-slim

# Metadados
LABEL maintainer="Ugarit Digital"
LABEL description="Engenheiro Kothar v4.0 — API Backend"

# Variáveis
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Dependências do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Dependências Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Código da aplicação
COPY . /app/backend

RUN addgroup --system kothar \
    && adduser --system --ingroup kothar --home /home/kothar kothar \
    && mkdir -p /data/cofre_rw \
    && chown -R kothar:kothar /data /app

USER kothar

# Porta
EXPOSE 8080

# Health check interno
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8080/health/ || exit 1

# Entry point
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8080"]
