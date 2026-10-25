import os

source_file = '/home/bruno/kothar/backend/api/routers/ollama_proxy.py'
with open(source_file, 'r') as f:
    lines = f.readlines()

def get_lines(start, end):
    return "".join(lines[start-1:end])

imports = get_lines(1, 48)

# 1. Criar pasta
os.makedirs('/home/bruno/kothar/backend/api/routers/ollama_proxy', exist_ok=True)

# 2. project_tools_api.py
with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/project_tools_api.py', 'w') as f:
    f.write(imports + "\n" + get_lines(876, 946))

# 3. system_routes.py
with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/system_routes.py', 'w') as f:
    f.write(imports + "\n" + get_lines(301, 347))

# 4. rag_injection.py
with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/rag_injection.py', 'w') as f:
    f.write(imports + "\n" + get_lines(527, 807))

# 5. worker.py
with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/worker.py', 'w') as f:
    f.write(imports + "\n" + get_lines(49, 226))

# 6. chat_proxy.py (O que sobrou, com imports arrumados)
chat_proxy_content = imports + """
from .worker import worker_state, ollama_background_worker
from .rag_injection import inject_rag_into_messages
""" + "\n" + get_lines(227, 300) + get_lines(349, 526) + get_lines(809, 874)

with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/chat_proxy.py', 'w') as f:
    f.write(chat_proxy_content)

# 7. __init__.py (Router Principal)
init_content = """
from fastapi import APIRouter
from .system_routes import router as system_router
from .project_tools_api import router as tools_router
from .chat_proxy import router as chat_router

router = APIRouter()
router.include_router(system_router)
router.include_router(tools_router)
router.include_router(chat_router)
"""
with open('/home/bruno/kothar/backend/api/routers/ollama_proxy/__init__.py', 'w') as f:
    f.write(init_content)

print("Split realizado com sucesso.")
