from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import List
from datetime import datetime, timezone
import uuid
import json
import os
from pathlib import Path

router = APIRouter()

class HeatmapPoint(BaseModel):
    x: int
    y: int
    value: float
    time: int
    type: str

class HeatmapPayload(BaseModel):
    project_id: str
    session_id: str
    url: str
    screen_width: int
    screen_height: int
    points: List[HeatmapPoint]

# Em um cenário de produção (Data Lake), isso iria para o PostgreSQL.
# Por enquanto, salvaremos fisicamente em JSON na pasta datasets do Kothar
# para que o Trace Frontend possa carregar rapidamente as matrizes de calor.

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = Path(
    os.environ.get("KOTHAR_HEATMAPS_PATH", str(PROJECT_ROOT / "datasets" / "heatmaps"))
).expanduser()
DATA_DIR.mkdir(parents=True, exist_ok=True)

def save_points_to_disk(payload: HeatmapPayload):
    try:
        # Agrupa por projeto e URL (substituindo barras)
        safe_url = payload.url.replace("/", "_")
        if not safe_url: safe_url = "home"
        
        file_path = DATA_DIR / f"{payload.project_id}_{safe_url}.json"
        
        existing_data = []
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    pass
        
        # Adiciona novos pontos
        for p in payload.points:
            existing_data.append({
                "x": p.x,
                "y": p.y,
                "value": p.value,
                "type": p.type,
                "session": payload.session_id,
                "screen": f"{payload.screen_width}x{payload.screen_height}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(existing_data, f)
            
    except Exception as e:
        import logging
        logging.error(f"Failed to save heatmap points: {e}")

@router.post("/track")
async def track_heatmap(payload: HeatmapPayload, background_tasks: BackgroundTasks):
    """
    Recebe as coordenadas de cliques/hovers do frontend.
    Processamento em background para não bloquear o response (velocidade absoluta).
    """
    background_tasks.add_task(save_points_to_disk, payload)
    return {"status": "ok"}

@router.get("/data/{project_id}")
async def get_heatmap_data(project_id: str, url: str = "home"):
    """
    Retorna os pontos para renderização no painel Controle de Temperatura.
    """
    safe_url = url.replace("/", "_")
    if not safe_url: safe_url = "home"
    file_path = DATA_DIR / f"{project_id}_{safe_url}.json"
    
    if not file_path.exists():
        return {"project": project_id, "url": url, "points": []}
        
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Para o plugin do heatmap, precisamos formatar os dados
            # Apenas um max abstrato, ajustável dinamicamente no frontend
            return {"project": project_id, "url": url, "points": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
