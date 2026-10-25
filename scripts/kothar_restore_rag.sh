#!/bin/bash
# =========================================================================
# KOTHAR v4.0 - RAG Restore Script
# Função: Injeta os vetores e grafos de volta no banco de dados lendo os
# arquivos frios salvos em ~/cofre/rag_backup/
# =========================================================================

BACKUP_DIR="$HOME/cofre/rag_backup"

if [ -z "$1" ]; then
    echo "Uso: $0 <data_do_backup_YYYY-MM-DD>"
    echo "Backups disponíveis:"
    ls -1 "$BACKUP_DIR" | grep .tar.gz
    exit 1
fi

TARGET_BACKUP="backup_$1.tar.gz"

if [ ! -f "$BACKUP_DIR/$TARGET_BACKUP" ]; then
    echo "[Erro] Backup $TARGET_BACKUP não encontrado."
    exit 1
fi

echo "[Kothar Restore] Descompactando backup..."
cd "$BACKUP_DIR"
tar -xzf "$TARGET_BACKUP"

echo "[Kothar Restore] Restaurando banco..."

# Restauro Postgres (se usado para RAG/Traces)
if [ -f "$BACKUP_DIR/backup_$1/postgres_rag.dump" ]; then
    docker cp "$BACKUP_DIR/backup_$1/postgres_rag.dump" kothar_postgres:/tmp/
    docker exec kothar_postgres pg_restore -U kothar -d kothar_trace -1 -c /tmp/postgres_rag.dump
    echo "[Kothar Restore] Postgres restaurado."
fi

# Limpeza
rm -rf "$BACKUP_DIR/backup_$1"

echo "[Kothar Restore] Operação crítica concluída. A memória do orquestro foi restabelecida."
