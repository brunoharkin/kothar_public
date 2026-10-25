from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_active_chat_router_does_not_import_process_memory_worker():
    source = (ROOT / 'backend/api/routers/ollama_proxy/chat_proxy.py').read_text()
    assert 'from .worker import' not in source
    assert 'worker_state.sessions' not in source
    assert 'worker_state.queue' not in source
    assert 'Fila assíncrona temporariamente indisponível' in source
    assert not (ROOT / 'backend/api/routers/ollama_proxy/worker.py').exists()


def test_frontend_uses_authenticated_direct_stream():
    source = (ROOT / 'frontend/src/paginas/ollama/ollama.api.ts').read_text()
    assert '/api/ollama/proxy/chat`' in source
    assert '/api/ollama/proxy/chat_async' not in source
