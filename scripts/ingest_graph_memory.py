"""
KOTHAR v4.0 - Script de Ingestão do GraphRAG
Lê as pastas /app/apps/ e joga a estrutura de arquivos no Neo4j
"""
import os
import re
import sys
import asyncio
from pathlib import Path

sys.path.append('/app')
from backend.core.database import get_neo4j_session

APPS_DIR = Path('/app/apps')

async def run_ingestion():
    if not APPS_DIR.exists():
        print("⚠️  Diretório /app/apps/ não existe. Esqueceu de montar no docker-compose?")
        return

    apps = [d for d in APPS_DIR.iterdir() if d.is_dir()]
    print(f"🚀 Iniciando ingestão no Neo4j para {len(apps)} aplicações...")

    import_pattern = re.compile(r'^(?:import|from)\s+.*?(?:[\'"])(.*?)(?:[\'"])', re.MULTILINE)

    async with get_neo4j_session() as session:
        # Limpar grafo anterior
        await session.run("MATCH (n:App)-[r]->() DELETE r")
        await session.run("MATCH (n:App) DELETE n")
        await session.run("MATCH (n:File)-[r]->() DELETE r")
        await session.run("MATCH (n:File) DELETE n")
        await session.run("MATCH (n:Dependency) DELETE n")

        for app in apps:
            app_name = app.name
            print(f"📦 Mapeando {app_name}...")
            
            await session.run("MERGE (a:App {name: $name})", name=app_name)

            files_count = 0
            for root, dirs, files in os.walk(app):
                if any(ignored in root for ignored in ['node_modules', '.venv', '.git', 'dist', '__pycache__', '.next', 'build']):
                    continue
                
                for file in files:
                    if not file.endswith(('.py', '.ts', '.tsx', '.js', '.jsx', '.json')):
                        continue
                        
                    file_path = Path(root) / file
                    relative_path = str(file_path.relative_to(app))
                    
                    await session.run(
                        """
                        MERGE (f:File {path: $path})
                        ON CREATE SET f.name = $name, f.app = $app, f.ext = $ext
                        WITH f
                        MATCH (a:App {name: $app})
                        MERGE (a)-[:HAS_FILE]->(f)
                        """,
                        path=f"{app_name}/{relative_path}",
                        name=file,
                        app=app_name,
                        ext=file_path.suffix
                    )
                    files_count += 1
                    
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        imports = import_pattern.findall(content)
                        for imp in imports:
                            if not imp.startswith('.'):
                                await session.run(
                                    """
                                    MERGE (d:Dependency {name: $dep})
                                    WITH d
                                    MATCH (f:File {path: $path})
                                    MERGE (f)-[:DEPENDS_ON]->(d)
                                    """,
                                    dep=imp, path=f"{app_name}/{relative_path}"
                                )
                    except Exception:
                        pass
                        
            print(f"  ✓ {files_count} arquivos indexados.")
            
    print("✅ Ingestão de Grafo Concluída com Sucesso!")

if __name__ == "__main__":
    asyncio.run(run_ingestion())
