#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - RAG Backup Daemon
# Função: Aguarda 5 minutos após a inicialização e realiza o dump estrutural
# dos bancos vetoriais (Chroma) e Grafos (Neo4j/Codebase) para ~/cofre/rag_backup
# =========================================================================

echo "[Kothar Backup] Iniciando rotina de espera (5 minutos)..."
sleep 300 # Aguarda 5 minutos para os containers estabilizarem

BACKUP_DIR="$HOME/cofre/rag_backup"
DATE_STAMP=$(date +%Y-%m-%d)
BACKUP_PATH="$BACKUP_DIR/backup_$DATE_STAMP"

mkdir -p "$BACKUP_PATH"

echo "[Kothar Backup] Iniciando extração dos grafos e vetores..."

# Exemplo de extração lógica: se você estiver rodando Postgres (pgvector)
if docker ps | grep -q "kothar_postgres"; then
    docker exec kothar_postgres pg_dump -U kothar -d kothar_trace -F c -f /tmp/rag_backup.dump
    docker cp kothar_postgres:/tmp/rag_backup.dump "$BACKUP_PATH/postgres_rag.dump"
    echo "[Kothar Backup] Backup do Postgres concluído."
fi

# Se houver ChromaDB ou Neo4j mapeado em volume, copiaremos o volume físico ou usaremos API
# (Assumindo pastas locais padronizadas do docker-compose)
if [ -d "$HOME/kothar/data/chromadb" ]; then
    cp -r "$HOME/kothar/data/chromadb" "$BACKUP_PATH/chromadb_copy"
    echo "[Kothar Backup] Backup do ChromaDB concluído."
fi

# Empacotar
cd "$BACKUP_DIR"
tar -czf "backup_$DATE_STAMP.tar.gz" "backup_$DATE_STAMP"
rm -rf "backup_$DATE_STAMP"

echo "[Kothar Backup] Finalizado com sucesso: backup_$DATE_STAMP.tar.gz"
