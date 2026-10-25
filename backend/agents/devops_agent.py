"""
=============================================================
 KOTHAR v4.0 — Agente DevOps
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Mandamento #1: verificar porta ANTES de subir qualquer serviço.
 Gerencia containers Docker, verifica saúde dos serviços.
"""

import subprocess
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.devops")


class DevOpsAgent(BaseAgent):

    @property
    def description(self) -> str:
        return "DevOps — verifica portas, gerencia containers e infra"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        action = task.get("action", "check_ports")
        ports  = task.get("ports", [])
        service= task.get("service", "")

        if action == "check_ports":
            return await self._check_ports(ports)
        elif action == "docker_status":
            return await self._docker_status()
        elif action == "restart_service":
            return await self._restart_service(service)
        elif action == "check_health":
            return await self._check_health(task.get("url", ""))
        else:
            return {"status": "skipped", "action": action}

    async def _check_ports(self, ports: list[int]) -> dict[str, Any]:
        """Mandamento #1 — verifica se portas estão livres."""
        results = {}
        for port in ports:
            async with trace_recorder.trace_tool(
                self.session_id, self.agent_name, "check_port",
                tool_input={"port": port}
            ) as span:
                proc = subprocess.run(
                    f"lsof -i :{port} || echo 'LIVRE'",
                    shell=True, capture_output=True, text=True
                )
                is_free = "LIVRE" in proc.stdout or proc.stdout.strip() == ""
                results[str(port)] = "livre" if is_free else "em_uso"
                span["output"] = {"port": port, "status": results[str(port)]}

        conflitos = [p for p, s in results.items() if s == "em_uso"]
        if conflitos:
            log.warn("Portas em uso detectadas", portas=conflitos)

        return {"status": "done", "agent": self.agent_name, "ports": results, "conflicts": conflitos}

    async def _docker_status(self) -> dict[str, Any]:
        """Lista containers Kothar rodando."""
        async with trace_recorder.trace_tool(
            self.session_id, self.agent_name, "docker_ps"
        ) as span:
            proc = subprocess.run(
                "docker ps --filter name=kothar --format '{{.Names}}|{{.Status}}|{{.Ports}}'",
                shell=True, capture_output=True, text=True
            )
            containers = []
            for line in proc.stdout.strip().splitlines():
                if "|" in line:
                    parts = line.split("|")
                    containers.append({"name": parts[0], "status": parts[1], "ports": parts[2] if len(parts) > 2 else ""})
            span["output"] = {"containers": containers}
        return {"status": "done", "agent": self.agent_name, "containers": containers}

    async def _restart_service(self, service: str) -> dict[str, Any]:
        """Reinicia um container Docker."""
        async with trace_recorder.trace_tool(
            self.session_id, self.agent_name, "docker_restart",
            tool_input={"service": service}
        ) as span:
            proc = subprocess.run(
                f"docker restart {service}", shell=True, capture_output=True, text=True
            )
            span["output"] = {"returncode": proc.returncode, "output": proc.stdout}
        return {"status": "done", "agent": self.agent_name, "service": service, "returncode": proc.returncode}

    async def _check_health(self, url: str) -> dict[str, Any]:
        """Verifica health de um serviço HTTP."""
        import httpx
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(url)
                return {"status": "healthy", "code": resp.status_code, "url": url}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e), "url": url}
