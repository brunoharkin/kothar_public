"""
=============================================================
 KOTHAR v6.0 — Memória de Conversa Infinita
 Sumarização progressiva de mensagens antigas
 Persistência no cofre
=============================================================
"""
import os
import json
import time
import asyncio
import logging
import re
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger("kothar.memory")

COFRE_DIR = Path(
    os.environ.get(
        "KOTHAR_MEMORY_PATH",
        os.environ.get("KOTHAR_VAULT_PATH", "/home/bruno-harkin/Cofre") + "/kothar_memories",
    )
)
MEMORY_DIR = COFRE_DIR / "kothar_memories"
MEMORY_DIR.mkdir(parents=True, exist_ok=True)

# Configurações
RECENT_BUFFER = 10          # últimas N mensagens integrais
COMPRESS_THRESHOLD = 20     # comprime quando passa disso
SUMMARIZE_MODEL = "kothar-claude:latest"  # modelo para sumarizar conversas
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")


class ConversationMemory:
    """Memória persistente de conversa com sumarização."""

    def __init__(self, session_id: str):
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,100}", session_id):
            raise ValueError("session_id inválido")
        self.session_id = session_id
        self.memory_file = MEMORY_DIR / f"{session_id}.json"
        self.summary_file = MEMORY_DIR / f"{session_id}_summary.md"
        self._messages: List[Dict] = []
        self._summary: str = ""
        self._compression_count: int = 0
        self._load()

    def _load(self):
        if self.memory_file.exists():
            try:
                data = json.loads(self.memory_file.read_text(encoding="utf-8"))
                self._messages = data.get("messages", [])
                self._summary = data.get("summary", "")
                self._compression_count = data.get("compression_count", 0)
            except Exception as e:
                logger.warning(f"Falha ao carregar memória de {self.session_id}: {e}")

    def _save(self):
        try:
            data = {
                "session_id": self.session_id,
                "messages": self._messages[-RECENT_BUFFER:],
                "summary": self._summary,
                "compression_count": self._compression_count,
                "updated_at": time.time(),
            }
            self.memory_file.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            # Salva summary como markdown também (legível)
            if self._summary:
                self.summary_file.write_text(
                    f"# Memória de Sessão {self.session_id}\n\n{self._summary}\n",
                    encoding="utf-8",
                )
        except Exception as e:
            logger.warning(f"Falha ao salvar memória: {e}")

    def add_message(self, role: str, content: str):
        """Adiciona mensagem e dispara compressão se necessário."""
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        if len(self._messages) >= COMPRESS_THRESHOLD:
            self._compress_sync()
        self._save()

    async def add_message_async(self, role: str, content: str):
        """Versão async."""
        self._messages.append({
            "role": role,
            "content": content,
            "timestamp": time.time(),
        })
        if len(self._messages) >= COMPRESS_THRESHOLD:
            await self._compress_async()
        self._save()

    def _compress_sync(self):
        """Compressão síncrona (fallback)."""
        if len(self._messages) <= RECENT_BUFFER:
            return

        # Pega mensagens antigas (que serão removidas do buffer)
        old_messages = self._messages[:-RECENT_BUFFER]

        # Sumariza de forma simples (sem LLM) — extrai tópicos-chave
        new_summary = self._extract_topics(old_messages)
        if self._summary:
            self._summary = f"{self._summary}\n\n---\n\n{new_summary}"
        else:
            self._summary = new_summary

        self._compression_count += 1
        self._messages = self._messages[-RECENT_BUFFER:]
        logger.info(
            f"Memória {self.session_id}: comprimida "
            f"({len(old_messages)} msgs → resumo, {self._compression_count}ª compressão)"
        )

    async def _compress_async(self):
        """Compressão usando o modelo Ollama para gerar resumo real."""
        if len(self._messages) <= RECENT_BUFFER:
            return

        old_messages = self._messages[:-RECENT_BUFFER]
        messages_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:300]}" for m in old_messages
        )

        summary_prompt = f"""Resuma esta conversa de forma estruturada, mantendo:
1. Tópicos principais discutidos
2. Decisões ou conclusões importantes
3. Nomes de entidades mencionadas (projetos, pessoas, sistemas)
4. Próximos passos acordados

Conversa:
{messages_text[:4000]}

Resumo estruturado:"""

        try:
            import httpx
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    f"{OLLAMA_URL}/api/generate",
                    json={
                        "model": SUMMARIZE_MODEL,
                        "prompt": summary_prompt,
                        "stream": False,
                        "options": {"num_predict": 500, "temperature": 0.3},
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    llm_summary = data.get("response", "").strip()
                    if llm_summary:
                        if self._summary:
                            self._summary = f"{self._summary}\n\n---\n\n{llm_summary}"
                        else:
                            self._summary = llm_summary
                        self._compression_count += 1
                        self._messages = self._messages[-RECENT_BUFFER:]
                        logger.info(
                            f"Memória {self.session_id}: comprimida via LLM "
                            f"({self._compression_count}ª vez)"
                        )
                        return
        except Exception as e:
            logger.warning(f"Sumarização via LLM falhou, usando extração simples: {e}")

        # Fallback
        self._compress_sync()

    def _extract_topics(self, messages: List[Dict]) -> str:
        """Extração simples de tópicos (sem LLM)."""
        topics = []
        for m in messages[:30]:
            if m["role"] == "user":
                content = m["content"][:150].replace("\n", " ")
                topics.append(f"- {content}")

        summary = f"## Compressão #{self._compression_count + 1} ({len(messages)} mensagens)\n\n"
        summary += "**Perguntas/tópicos do usuário:**\n"
        summary += "\n".join(topics[:20])
        return summary

    def get_context(self) -> str:
        """Retorna contexto formatado para injeção no system prompt."""
        parts = []

        if self._summary:
            parts.append("# === MEMÓRIA DE CONVERSAS ANTERIORES ===")
            parts.append(
                f"Esta sessão já tem {self._compression_count} compressão(ões). "
                "Resumo acumulado do que foi discutido antes:"
            )
            parts.append(self._summary[:3000])  # limita tamanho
            parts.append("# === FIM DA MEMÓRIA ===\n")

        if self._messages:
            parts.append("# === ÚLTIMAS MENSAGENS DA CONVERSA ATUAL ===")
            for m in self._messages[-RECENT_BUFFER:]:
                content = m["content"][:500] if isinstance(m["content"], str) else str(m["content"])[:500]
                parts.append(f"{m['role'].upper()}: {content}")
            parts.append("# === FIM DAS MENSAGENS RECENTES ===\n")

        return "\n".join(parts)

    def get_stats(self) -> Dict:
        return {
            "session_id": self.session_id,
            "total_messages": len(self._messages),
            "compression_count": self._compression_count,
            "summary_chars": len(self._summary),
            "memory_file": str(self.memory_file),
        }


# === SINGLETON CACHE ===
_memories: Dict[str, ConversationMemory] = {}


def get_memory(session_id: str) -> ConversationMemory:
    """Retorna instância de memória para a sessão (cached)."""
    if session_id not in _memories:
        _memories[session_id] = ConversationMemory(session_id)
    return _memories[session_id]


def clear_memory_cache():
    """Limpa cache de memórias (útil para testes)."""
    _memories.clear()
