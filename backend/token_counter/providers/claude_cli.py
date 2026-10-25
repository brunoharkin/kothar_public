"""
Claude CLI Provider - Leitura de uso via CLI
=============================================

Inspirado em ClaudeUsageCLI.swift do Codenotch.

Este provider executa `claude /usage` como subprocesso para obter
dados de consumo sem precisar de acesso ao keychain.

Fluxo:
1. Localizar binário claude em paths conhecidos
2. Executar comando com argumentos específicos
3. Parsear saída para extrair percentages e datas de reset
4. Retornar ProviderSnapshot com os dados
"""

from __future__ import annotations

import asyncio
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

from token_counter.models import (
    Fidelity,
    LimitWindow,
    ProviderSnapshot,
    ProviderStatus,
    UsageContext,
    WindowType,
)
from token_counter.providers.base import (
    BaseUsageProvider,
    ProviderKind,
    UsageProviderError,
)


class ClaudeCLIProvider(BaseUsageProvider):
    """
    Provider que lê dados de uso do Claude via CLI.

    Executa `claude /usage` e parseia a saída para extrair
    informações de consumo de tokens.

    Vantagem: não precisa de acesso ao keychain — o próprio
    Claude Code CLI já tem as credenciais.
    """

    # Paths conhecidos onde o binário claude pode estar instalado
    BINARY_PATHS = [
        "~/.local/bin/claude",
        "~/.claude/local/claude",
        "~/.bun/bin/claude",
        "~/.volta/bin/claude",
        "~/.nvm/versions/node/*/bin/claude",  # NVM
        "~/.local/share/fnm/node-versions/*/installation/bin/claude",  # FNM
        "~/.local/share/bun/installations/bun-*/bin/claude",  # BUN installations
        "~/.local/share/npm*/bin/claude",  # npm global
        "/opt/homebrew/bin/claude",
        "/usr/local/bin/claude",
    ]

    # Regex para parsear saída do `claude /usage`
    # Exemplo: "Current session: 38% used · resets Sep 7 at 2:59pm"
    USAGE_LINE_PATTERN = re.compile(
        r"(?:Current\s+)?(?P<type>session|week|month|daily)s?\s*(?:\([^)]+\))?:\s*"
        r"(?P<percent>\d+)%\s*used\s*"
        r"·\s*resets\s+(?P<reset>.+?)(?:\s*\(|$)",
        re.IGNORECASE,
    )

    # Regex alternativa mais simples
    SIMPLE_USAGE_PATTERN = re.compile(
        r"(?P<type>session|week|month|daily)s?\s*(?:\([^)]+\))?:\s*"
        r"(?P<percent>\d+)%\s*used",
        re.IGNORECASE,
    )

    def __init__(self):
        self._binary_path: Optional[str] = None
        self._last_fetch: Optional[datetime] = None
        self._last_output: Optional[str] = None

    @property
    def id(self) -> str:
        return "claude-cli"

    @property
    def display_name(self) -> str:
        return "Claude Code"

    @property
    def kind(self):
        from token_counter.providers.base import ProviderKind
        return ProviderKind.USAGE

    def glyph(self) -> str:
        return "🔮"

    def is_available(self) -> bool:
        """Verifica se o binário claude está disponível."""
        return self._find_binary() is not None

    def _find_binary(self) -> Optional[str]:
        """
        Procura o binário claude em uma lista de paths conhecidos.

        Returns:
            Caminho do binário se encontrado, None caso contrário
        """
        if self._binary_path:
            return self._binary_path

        # Tenta 'which' primeiro (mais rápido)
        claude_path = shutil.which("claude")
        if claude_path and os.path.isfile(claude_path):
            self._binary_path = claude_path
            return claude_path

        # Tenta paths conhecidos
        for pattern in self.BINARY_PATHS:
            expanded = os.path.expanduser(pattern)

            # Wildcard expansion para version managers
            if "*" in expanded:
                matches = sorted(Path(os.path.dirname(expanded)).glob(os.path.basename(expanded)))
                for match in matches:
                    if match.is_file():
                        self._binary_path = str(match)
                        return str(match)
            else:
                if os.path.isfile(expanded):
                    self._binary_path = expanded
                    return expanded

        return None

    async def fetch_snapshot(self) -> ProviderSnapshot:
        """
        Executa `claude /usage` e parseia a saída.

        Returns:
            ProviderSnapshot com dados de uso

        Raises:
            UsageProviderError: Se o binário não for encontrado ou falhar
        """
        binary_path = self._find_binary()

        if not binary_path:
            raise UsageProviderError.unsupported(
                "Claude Code binary not found"
            )

        try:
            # Executa o comando com argumentos específicos
            # --print: saída direta, sem UI
            # --strict-mcp-config: evita iniciar servidores MCP desnecessários
            # --no-session-persistence: sem transcrição
            cmd = [
                binary_path,
                "--print",
                "--no-session-persistence",
                "--strict-mcp-config",
                "/usage",
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(),
                    timeout=30.0,  # 30 segundos de timeout
                )
            except asyncio.TimeoutError:
                process.kill()
                raise UsageProviderError.timeout(
                    "Claude /usage command timed out"
                )

            if process.returncode != 0:
                stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""
                raise UsageProviderError.unknown(
                    f"Claude /usage failed: {stderr_text}"
                )

            output = stdout.decode("utf-8", errors="replace")
            self._last_output = output
            self._last_fetch = datetime.now()

            # Parseia a saída
            windows = self._parse_usage_output(output)

            context = UsageContext(
                timestamp=datetime.now(),
                instance="claude-cli",
            )

            return ProviderSnapshot(
                id=self.id,
                name=self.display_name,
                fidelity=Fidelity.OFFICIAL,
                status=ProviderStatus.OK,
                windows=windows,
                context=context,
            )

        except UsageProviderError:
            raise
        except Exception as e:
            raise UsageProviderError.unknown(str(e))

    def _parse_usage_output(self, output: str) -> list[LimitWindow]:
        """
        Parseia a saída do comando `claude /usage`.

        Exemplos de entrada:
            "Current session: 38% used · resets Sep 7 at 2:59pm (Asia/Jakarta)"
            "Current week (all models): 4% used · resets Sep 14 at 5:59am (Asia/Jakarta)"

        Returns:
            Lista de LimitWindow com os dados parseados
        """
        windows = []

        # Tenta primeiro o pattern completo com resets
        for match in self.USAGE_LINE_PATTERN.finditer(output):
            window_type = self._parse_window_type(match.group("type"))
            percent = int(match.group("percent"))
            reset_str = match.group("reset").strip() if match.group("reset") else None

            window = LimitWindow(
                type=window_type,
                used_fraction=percent / 100.0,
                used=0,  # Não temos valores absolutos, só percentual
                limit=100,
                remaining=100 - percent,
                resets_at=self._parse_reset_date(reset_str) if reset_str else None,
            )
            windows.append(window)

        # Fallback: tenta pattern simples
        if not windows:
            for match in self.SIMPLE_USAGE_PATTERN.finditer(output):
                window_type = self._parse_window_type(match.group("type"))
                percent = int(match.group("percent"))

                window = LimitWindow(
                    type=window_type,
                    used_fraction=percent / 100.0,
                    used=0,
                    limit=100,
                    remaining=100 - percent,
                )
                windows.append(window)

        return windows

    def _parse_window_type(self, type_str: str) -> WindowType:
        """Converte string de tipo para WindowType."""
        type_lower = type_str.lower().strip()

        if "session" in type_lower:
            return WindowType.SESSION
        elif "week" in type_lower:
            return WindowType.WEEKLY
        elif "month" in type_lower:
            return WindowType.MONTHLY
        elif "daily" in type_lower or "day" in type_lower:
            return WindowType.DAILY
        else:
            return WindowType.SESSION  # Default

    def _parse_reset_date(self, reset_str: str) -> Optional[datetime]:
        """
        Parseia string de reset para datetime.

        Exemplos:
            "Sep 7 at 2:59pm"
            "September 14 at 5:59am"
            "Sep 7 at 2:59pm (Asia/Jakarta)"
        """
        # Remove timezone se presente
        reset_str = re.sub(r"\s*\([^)]+\)\s*$", "", reset_str).strip()

        # Tenta formatos comuns
        formats = [
            "%b %d at %I:%M%p",      # Sep 7 at 2:59pm
            "%B %d at %I:%M%p",      # September 14 at 5:59am
            "%b %d at %H:%M",        # Sep 7 at 14:59
            "%B %d at %H:%M",        # September 14 at 14:59
            "%Y-%m-%d at %H:%M:%S",  # 2026-09-07 at 14:59:00
        ]

        for fmt in formats:
            try:
                naive_dt = datetime.strptime(reset_str, fmt)
                # Assume timezone local - combina com data atual
                now = datetime.now()
                reset_dt = naive_dt.replace(year=now.year)

                # Se a data já passou este ano, assume próximo ano
                if reset_dt < now:
                    reset_dt = reset_dt.replace(year=now.year + 1)

                return reset_dt
            except ValueError:
                continue

        return None

    def get_last_output(self) -> Optional[str]:
        """Retorna a última saída do comando (para debug)."""
        return self._last_output

    def get_last_fetch(self) -> Optional[datetime]:
        """Retorna timestamp da última busca."""
        return self._last_fetch
