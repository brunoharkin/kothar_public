#!/usr/bin/env python3
"""
KOTHAR BACKUP SYSTEM
Backup automatizado para projetos e configurações
"""

import os
import sys
import json
import tarfile
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# Config
BACKUP_DIR = Path.home() / ".kothar" / "backups"
PROJECTS_DIR = Path.home()
KOTHAR_CONFIG_DIR = Path.home() / ".claude"

# Portas para verificar antes de backup
PORTS_TO_CHECK = {
    "disparo-em-massa": {"postgres": 5432, "evolution": 2786},
    "crm-saphia": {"postgres": 5433, "redis": 6380, "evolution": 2785},
    "orby-ia": {"postgres": 5440, "redis": 6381},
}

class KotharBackup:
    """Sistema de backup Kothar"""

    def __init__(self):
        self.backup_dir = BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def check_port_available(self, port: int) -> bool:
        """Verifica se porta está livre"""
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) != 0

    def backup_chromadb(self) -> Optional[str]:
        """Backup do ChromaDB"""
        chromadb_path = Path(os.environ.get("KOTHAR_CHROMA_DATA_PATH", Path.home() / "kothar" / ".chroma-data"))
        if not chromadb_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"chromadb_{timestamp}.tar.gz"

        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(chromadb_path, arcname="chromadb")

        return str(backup_file)

    def backup_config(self) -> Optional[str]:
        """Backup das configurações do Claude"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"config_{timestamp}.tar.gz"

        configs_to_backup = [
            KOTHAR_CONFIG_DIR / "settings.json",
            KOTHAR_CONFIG_DIR / "agents",
            KOTHAR_CONFIG_DIR / "references",
            KOTHAR_CONFIG_DIR / "skills",
        ]

        with tarfile.open(backup_file, "w:gz") as tar:
            for config in configs_to_backup:
                if config.exists():
                    tar.add(config, arcname=str(config.relative_to(Path.home())))

        return str(backup_file)

    def backup_memory(self) -> Optional[str]:
        """Backup das memórias"""
        memory_path = Path.home() / ".claude" / "projects" / "-home-bruno-kothar" / "memory"
        if not memory_path.exists():
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"memory_{timestamp}.tar.gz"

        with tarfile.open(backup_file, "w:gz") as tar:
            tar.add(memory_path, arcname="memory")

        return str(backup_file)

    def verify_postgres_backup(self, port: int) -> bool:
        """Verifica integridade do backup PostgreSQL"""
        # Simulado - em produção seria: pg_dump --dbname=... --schema-only
        return self.check_port_available(port)

    def run_full_backup(self) -> Dict[str, any]:
        """Executa backup completo"""
        results = {
            "timestamp": datetime.now().isoformat(),
            "success": True,
            "backups": {},
            "errors": []
        }

        # Backup ChromaDB
        try:
            chromadb_backup = self.backup_chromadb()
            if chromadb_backup:
                results["backups"]["chromadb"] = chromadb_backup
        except Exception as e:
            results["errors"].append(f"ChromaDB: {str(e)}")

        # Backup Config
        try:
            config_backup = self.backup_config()
            if config_backup:
                results["backups"]["config"] = config_backup
        except Exception as e:
            results["errors"].append(f"Config: {str(e)}")

        # Backup Memory
        try:
            memory_backup = self.backup_memory()
            if memory_backup:
                results["backups"]["memory"] = memory_backup
        except Exception as e:
            results["errors"].append(f"Memory: {str(e)}")

        if results["errors"]:
            results["success"] = False

        return results

    def list_backups(self) -> List[Dict]:
        """Lista backups disponíveis"""
        backups = []
        for backup_file in self.backup_dir.glob("*.tar.gz"):
            stat = backup_file.stat()
            backups.append({
                "name": backup_file.name,
                "size": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def restore_backup(self, backup_file: str, component: str) -> bool:
        """Restaura um backup específico"""
        backup_path = Path(backup_file)
        if not backup_path.exists():
            return False

        try:
            with tarfile.open(backup_path, "r:gz") as tar:
                # Extrai para diretório temporário primeiro
                import tempfile
                with tempfile.TemporaryDirectory() as tmpdir:
                    tar.extractall(tmpdir)

                    # Move para destino
                    extracted = Path(tmpdir) / component
                    if extracted.exists():
                        dest = {
                            "chromadb": Path(os.environ.get("KOTHAR_CHROMA_DATA_PATH", Path.home() / "kothar" / ".chroma-data")),
                            "config": Path.home() / ".claude",
                            "memory": Path.home() / ".claude" / "projects" / "-home-bruno-kothar" / "memory"
                        }.get(component)

                        if dest:
                            import shutil
                            if dest.exists():
                                shutil.rmtree(dest)
                            shutil.copytree(extracted, dest)
                            return True
        except Exception:
            return False

        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(description="Kothar Backup System")
    parser.add_argument("action", choices=["backup", "restore", "list"],
                        help="Ação a executar")
    parser.add_argument("--component", choices=["chromadb", "config", "memory", "all"],
                        default="all", help="Componente para backup/restore")
    parser.add_argument("--file", help="Arquivo de backup para restore")

    args = parser.parse_args()

    backup = KotharBackup()

    if args.action == "backup":
        results = backup.run_full_backup()
        print(json.dumps(results, indent=2))

    elif args.action == "list":
        backups = backup.list_backups()
        print(json.dumps(backups, indent=2))

    elif args.action == "restore":
        if not args.file:
            print("Erro: --file é obrigatório para restore")
            sys.exit(1)
        success = backup.restore_backup(args.file, args.component)
        print(json.dumps({"success": success}))

if __name__ == "__main__":
    main()
