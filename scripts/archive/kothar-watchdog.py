#!/usr/bin/env python3
"""
KOTHAR WATCHDOG - Vigilante 24/7 do Sistema
Monitora recursos, protege contra travamentos, gerencia processos
"""

import os
import sys
import json
import time
import subprocess
import threading
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import List, Optional

# Carregar .env
env_file = Path(__file__).parent.parent / ".env"
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            if "=" in line and not line.startswith("#"):
                key, val = line.strip().split("=", 1)
                os.environ[key] = val

import psutil
import requests

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Thresholds:
    CPU_WARN: float = 80.0      # % CPU para aviso
    CPU_CRITICAL: float = 95.0  # % CPU para ação
    MEMORY_WARN: float = 80.0   # % Memória para aviso
    MEMORY_CRITICAL: float = 92.0  # % Memória para ação
    DISK_WARN: float = 85.0     # % Disco para aviso
    PROCESS_LIMIT: int = 50      # Número máximo de processos ativos

@dataclass
class WatchdogConfig:
    enabled: bool = True
    auto_cleanup_cache: bool = True       # Limpa cache automaticamente
    auto_cleanup_logs: bool = True        # Limpa logs automaticamente
    log_retention_days: int = 1          # Manter apenas 1 dia de logs
    auto_kill_idle: bool = False         # Só mata com permissão
    telegram_alerts: bool = True
    log_level: str = "INFO"
    check_interval: int = 10             # segundos
    priority_keywords: List[str] = None   # Processos prioritários

    def __post_init__(self):
        if self.priority_keywords is None:
            self.priority_keywords = ["whisper", "python", "transcri", "kothar", "claude"]

config = WatchdogConfig()

# ═══════════════════════════════════════════════════════════════════════════
# STATUS DO SISTEMA
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class SystemStatus:
    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    memory_total_gb: float
    disk_percent: float
    processes_count: int
    top_cpu_processes: List[dict]
    top_memory_processes: List[dict]
    warnings: List[str]
    criticals: List[str]

class SystemMonitor:
    """Monitor de recursos do sistema"""

    def __init__(self):
        self.thresholds = Thresholds()
        self.last_alert_time = {}

    def get_status(self) -> SystemStatus:
        """Coleta status completo do sistema"""

        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memória
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = round(memory.available / (1024**3), 2)
        memory_total_gb = round(memory.total / (1024**3), 2)

        # Disco
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        # Processos
        processes = list(psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']))
        processes_count = len(processes)

        # Top processos por CPU
        top_cpu = []
        for p in sorted(processes, key=lambda x: x.info['cpu_percent'] or 0, reverse=True)[:5]:
            try:
                top_cpu.append({
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'cpu': round(p.info['cpu_percent'] or 0, 1),
                    'mem': round(p.info['memory_percent'] or 0, 1)
                })
            except:
                pass

        # Top processos por Memória
        top_mem = []
        for p in sorted(processes, key=lambda x: x.info['memory_percent'] or 0, reverse=True)[:5]:
            try:
                top_mem.append({
                    'pid': p.info['pid'],
                    'name': p.info['name'],
                    'cpu': round(p.info['cpu_percent'] or 0, 1),
                    'mem': round(p.info['memory_percent'] or 0, 1)
                })
            except:
                pass

        # Análise de avisos
        warnings = []
        criticals = []

        if cpu_percent >= self.thresholds.CPU_CRITICAL:
            criticals.append(f"🔥 CPU CRÍTICA: {cpu_percent}%")
        elif cpu_percent >= self.thresholds.CPU_WARN:
            warnings.append(f"⚠️ CPU alta: {cpu_percent}%")

        if memory_percent >= self.thresholds.MEMORY_CRITICAL:
            criticals.append(f"🔥 MEMÓRIA CRÍTICA: {memory_percent}%")
        elif memory_percent >= self.thresholds.MEMORY_WARN:
            warnings.append(f"⚠️ Memória alta: {memory_percent}%")

        if disk_percent >= self.thresholds.DISK_WARN:
            warnings.append(f"⚠️ Disco: {disk_percent}%")

        return SystemStatus(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            cpu_percent=round(cpu_percent, 1),
            memory_percent=round(memory_percent, 1),
            memory_available_gb=memory_available_gb,
            memory_total_gb=memory_total_gb,
            disk_percent=round(disk_percent, 1),
            processes_count=processes_count,
            top_cpu_processes=top_cpu,
            top_memory_processes=top_mem,
            warnings=warnings,
            criticals=criticals
        )

    def is_priority_process(self, process_name: str) -> bool:
        """Verifica se é processo prioritário"""
        name_lower = process_name.lower()
        for keyword in config.priority_keywords:
            if keyword.lower() in name_lower:
                return True
        return False

    def get_status_text(self, status: SystemStatus) -> str:
        """Formata status para Telegram"""
        text = f"""
🔍 **KOTHAR WATCHDOG** - {status.timestamp}

**💻 RECURSOS**
├ CPU: {status.cpu_percent}%
├ RAM: {status.memory_percent}% ({status.memory_available_gb}GB livre de {status.memory_total_gb}GB)
├ Disco: {status.disk_percent}%
└ Processos: {status.processes_count}

"""
        if status.criticals:
            text += "**🚨 CRÍTICO**\n"
            for c in status.criticals:
                text += f"• {c}\n"
            text += "\n"

        if status.warnings:
            text += "**⚠️ AVISOS**\n"
            for w in status.warnings:
                text += f"• {w}\n"
            text += "\n"

        text += "**🔥 TOP CPU**\n"
        for p in status.top_cpu_processes[:3]:
            emoji = "⭐" if self.is_priority_process(p['name']) else "•"
            text += f"{emoji} {p['name']}: {p['cpu']}%\n"

        text += "\n**💾 TOP MEMÓRIA**\n"
        for p in status.top_memory_processes[:3]:
            emoji = "⭐" if self.is_priority_process(p['name']) else "•"
            text += f"{emoji} {p['name']}: {p['mem']}%\n"

        return text.strip()

# ═══════════════════════════════════════════════════════════════════════════
# GERENCIADOR DE PROCESSOS
# ═══════════════════════════════════════════════════════════════════════════

class ProcessManager:
    """Gerenciador de processos com inteligência"""

    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.process_history = {}  # Track processos por nome
        self.protected_processes = [
            "systemd", "init", "ssh", "docker",
            "kothar-watchdog",
            "gnome", "xorg", "pulseaudio"
        ]

    def find_processes_to_kill(self, status: SystemStatus) -> List[dict]:
        """Encontra processos que podem ser encerrados"""
        candidates = []

        for p in status.top_memory_processes:
            # Pular processos protegidos
            if any(prot in p['name'].lower() for prot in self.protected_processes):
                continue

            # Pular processos prioritários
            if self.monitor.is_priority_process(p['name']):
                continue

            # Processos que podem ser encerrados
            safe_kill = [
                "chrome", "firefox", "brave", "electron",
                "spotify", "discord", "slack", "teams",
                "code", "code-insiders", "sublime", "atom",
                "node", "npm", "yarn", "bundle",
                "terraform", "ansible", "vagrant"
            ]

            if any(safe in p['name'].lower() for safe in safe_kill):
                if p['mem'] > 1.0:  # Mais de 1% memória
                    candidates.append({
                        'pid': p['pid'],
                        'name': p['name'],
                        'reason': f"Memória alta: {p['mem']}%",
                        'safe': True
                    })

        return candidates

    def kill_process(self, pid: int, reason: str = "") -> bool:
        """Encerra processo com segurança"""
        try:
            proc = psutil.Process(pid)
            name = proc.name()

            # Verificar se é protegido
            if any(prot in name.lower() for prot in self.protected_processes):
                return False

            proc.terminate()
            try:
                proc.wait(timeout=5)
            except psutil.TimeoutExpired:
                proc.kill()

            return True
        except psutil.NoSuchProcess:
            return True
        except Exception as e:
            print(f"Erro ao matar processo {pid}: {e}")
            return False

    def cleanup_cache(self) -> dict:
        """Limpa cache do sistema"""
        results = {"cleared": [], "failed": [], "space_freed": 0}

        # Limpar cache do sistema (requer sudo)
        try:
            # PageCache
            result = subprocess.run(
                ["sync", "&&", "echo", "3", ">", "/proc/sys/vm/drop_caches"],
                shell=True, capture_output=True, timeout=10
            )
            results["cleared"].append("PageCache")
        except:
            pass

        # Limpar tmp
        try:
            temp_dirs = ["/tmp", "/var/tmp"]
            for tmp_dir in temp_dirs:
                if Path(tmp_dir).exists():
                    for item in Path(tmp_dir).glob("*"):
                        try:
                            size = item.stat().st_size if item.is_file() else 0
                            if item.is_file():
                                item.unlink()
                            elif item.is_dir():
                                import shutil
                                shutil.rmtree(item)
                            results["cleared"].append(str(item.name))
                            results["space_freed"] += size
                        except:
                            pass
        except:
            pass

        return results

    def cleanup_logs(self, retention_days: int = 1) -> dict:
        """Limpa logs do sistema - mantém apenas arquivos mais novos que retention_days"""
        from datetime import datetime, timedelta

        results = {"cleared": [], "space_freed": 0, "errors": []}

        cutoff_time = datetime.now() - timedelta(days=retention_days)

        log_dirs = [
            "/var/log",
            "/tmp",
            "/var/tmp",
        ]

        # Não tocar nestas pastas
        protected_patterns = [
            "private",
            "journal",
            ".cache"
        ]

        for log_dir in log_dirs:
            if not Path(log_dir).exists():
                continue

            for item in Path(log_dir).rglob("*"):
                try:
                    # Pular protegidos
                    if any(prot in str(item) for prot in protected_patterns):
                        continue

                    if item.is_file():
                        # Verificar idade do arquivo
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime < cutoff_time:
                            size = item.stat().st_size
                            item.unlink()
                            results["cleared"].append(f"{item.name} ({mtime.strftime('%d/%m')})")
                            results["space_freed"] += size

                    elif item.is_dir() and item.name.startswith("."):
                        # Limpar dirs ocultos velhos em /tmp
                        mtime = datetime.fromtimestamp(item.stat().st_mtime)
                        if mtime < cutoff_time:
                            import shutil
                            total_size = sum(
                                f.stat().st_size for f in item.rglob("*") if f.is_file()
                            )
                            shutil.rmtree(item)
                            results["cleared"].append(f"dir: {item.name}")
                            results["space_freed"] += total_size

                except Exception as e:
                    pass

        # Limpar journalctl com limite de tempo
        try:
            result = subprocess.run(
                ["journalctl", "--vacuum-time=1days"],
                capture_output=True, timeout=30
            )
            if result.returncode == 0:
                results["cleared"].append("journal: entries > 1 dia")
        except:
            pass

        # Limpar thumbnails velhos
        try:
            thumb_dir = Path.home() / ".cache" / "thumbnails"
            if thumb_dir.exists():
                for item in thumb_dir.rglob("*"):
                    try:
                        if item.is_file():
                            mtime = datetime.fromtimestamp(item.stat().st_mtime)
                            if mtime < cutoff_time:
                                results["space_freed"] += item.stat().st_size
                                item.unlink()
                                results["cleared"].append(f"thumb: {item.name}")
                    except:
                        pass
        except:
            pass

        # Converter bytes para formato legível
        if results["space_freed"] > 1024**3:
            results["space_freed_str"] = f"{results['space_freed'] / (1024**3):.2f} GB"
        elif results["space_freed"] > 1024**2:
            results["space_freed_str"] = f"{results['space_freed'] / (1024**2):.2f} MB"
        elif results["space_freed"] > 1024:
            results["space_freed_str"] = f"{results['space_freed'] / 1024:.2f} KB"
        else:
            results["space_freed_str"] = f"{results['space_freed']} B"

        return results

    def get_disk_usage(self) -> dict:
        """Retorna uso de disco por partição"""
        usage = {}
        for partition in psutil.disk_partitions():
            try:
                part_usage = psutil.disk_usage(partition.mountpoint)
                usage[partition.mountpoint] = {
                    "total_gb": round(part_usage.total / (1024**3), 2),
                    "used_gb": round(part_usage.used / (1024**3), 2),
                    "free_gb": round(part_usage.free / (1024**3), 2),
                    "percent": part_usage.percent
                }
            except:
                pass
        return usage

# ═══════════════════════════════════════════════════════════════════════════
# COMUNICADOR (Telegram)
# ═══════════════════════════════════════════════════════════════════════════

class AlertManager:
    """Gerenciador de alertas via Telegram"""

    def __init__(self):
        self.bot_token = os.environ.get("WATCHDOG_BOT_TOKEN", "")
        self.chat_id = os.environ.get("WATCHDOG_CHAT_ID", "")
        self.api_url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        self.alert_cooldown = 300  # 5 minutos entre alertas do mesmo tipo

    def send_alert(self, message: str, priority: str = "normal") -> bool:
        """Envia alerta via Telegram"""
        if not self.bot_token or not self.chat_id:
            print("⚠️ Telegram não configurado - exibindo localmente:")
            print(message)
            return False

        # Verificar cooldown
        alert_type = priority
        now = time.time()
        if alert_type in self.last_alert_time:
            if now - self.last_alert_time[alert_type] < self.alert_cooldown:
                return False

        try:
            response = requests.post(
                self.api_url,
                json={
                    "chat_id": self.chat_id,
                    "text": message,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True
                },
                timeout=10
            )

            if response.status_code == 200:
                self.last_alert_time[alert_type] = now
                return True
        except Exception as e:
            print(f"Erro ao enviar Telegram: {e}")

        return False

    def request_permission(self, action: str, details: str) -> bool:
        """Solicita permissão para ação"""
        message = f"""
⛔ **KOTHAR WATCHDOG - SOLICITAÇÃO DE PERMISSÃO**

{action}

{details}

_responda "sim" ou "não"_
"""
        return self.send_alert(message, priority="permission")

# ═══════════════════════════════════════════════════════════════════════════
# WATCHDOG PRINCIPAL
# ═══════════════════════════════════════════════════════════════════════════

class KotharWatchdog:
    """Vigilante principal do Kothar"""

    def __init__(self):
        self.monitor = SystemMonitor()
        self.process_manager = ProcessManager(self.monitor)
        self.alert_manager = AlertManager()
        self.running = False
        self.status_file = Path.home() / ".kothar" / "watchdog_status.json"
        self.status_file.parent.mkdir(parents=True, exist_ok=True)

    def save_status(self, status: SystemStatus):
        """Salva último status"""
        with open(self.status_file, 'w') as f:
            json.dump(asdict(status), f, indent=2)

    def check_and_act(self):
        """Verifica sistema e toma ações necessárias"""
        status = self.monitor.get_status()
        self.save_status(status)

        # Enviar status periodicamente (a cada 5 checks)
        if not hasattr(self, '_check_count'):
            self._check_count = 0
        self._check_count += 1

        # Sempre mostrar no console
        print(f"[{status.timestamp}] CPU: {status.cpu_percent}% | RAM: {status.memory_percent}% | Disco: {status.disk_percent}%")

        if status.criticals:
            print("  🚨 CRÍTICO:", ", ".join(status.criticals))
            self.alert_manager.send_alert(
                self.monitor.get_status_text(status),
                priority="critical"
            )

            # Auto-limpeza se memória crítica
            if "MEMÓRIA CRÍTICA" in status.criticals[0] and config.auto_cleanup_cache:
                print("  🧹 Auto-limpando cache...")
                results = self.process_manager.cleanup_cache()
                msg = f"✅ Cache limpo!\nItens: {len(results['cleared'])}"
                self.alert_manager.send_alert(msg, priority="info")

            # Auto-limpeza de LOGS se disco crítico
            if status.disk_percent >= 90 and config.auto_cleanup_logs:
                print("  📝 Auto-limpando logs velhos...")
                results = self.process_manager.cleanup_logs(retention_days=config.log_retention_days)
                msg = f"🧹 Logs limpos!\nEspaço: {results.get('space_freed_str', '0 B')}\nItens: {len(results['cleared'])}"
                self.alert_manager.send_alert(msg, priority="info")

        else:
            # Limpeza preventiva periódica (a cada 10 checks = ~2 minutos)
            if self._check_count % 10 == 0 and config.auto_cleanup_logs:
                results = self.process_manager.cleanup_logs(retention_days=config.log_retention_days)
                if len(results['cleared']) > 0:
                    print(f"  📝 Logs limpos preventivamente: {results.get('space_freed_str', '0 B')}")

            if status.warnings and self._check_count % 3 == 0:
                print("  ⚠️ Avisos:", ", ".join(status.warnings))
                self.alert_manager.send_alert(
                    self.monitor.get_status_text(status),
                    priority="warning"
                )

        # Verificar processos que podem ser encerrados
        if status.memory_percent >= self.monitor.thresholds.MEMORY_WARN:
            candidates = self.process_manager.find_processes_to_kill(status)
            if candidates and config.auto_kill_idle:
                for candidate in candidates[:3]:
                    msg = f"""
🧹 **PROCESSO CANDIDATO A ENCERRAMENTO**

Processo: *{candidate['name']}* (PID: {candidate['pid']})
Motivo: {candidate['reason']}

Posso encerrar? (sim/não)
"""
                    # Não encerra automaticamente - apenas notifica
                    self.alert_manager.send_alert(msg, priority="suggestion")

    def run(self):
        """Loop principal do watchdog"""
        print("=" * 60)
        print("🐕 KOTHAR WATCHDOG - VIGILANTE ATIVADO")
        print("=" * 60)
        print(f"⏱️  Intervalo: {config.check_interval}s")
        print(f"🧠 Prioridade: {', '.join(config.priority_keywords)}")
        print(f"💾 Auto-limpeza cache: {config.auto_cleanup_cache}")
        print("=" * 60)

        self.running = True

        while self.running:
            try:
                self.check_and_act()
                time.sleep(config.check_interval)
            except KeyboardInterrupt:
                print("\n⏹️ Encerrando watchdog...")
                self.running = False
                break
            except Exception as e:
                print(f"Erro no watchdog: {e}")
                time.sleep(config.check_interval)

        print("✅ Watchdog encerrado.")

    def stop(self):
        """Para o watchdog"""
        self.running = False

    def get_status(self) -> Optional[SystemStatus]:
        """Retorna último status salvo"""
        if self.status_file.exists():
            with open(self.status_file) as f:
                data = json.load(f)
                return SystemStatus(**data)
        return None


# ═══════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Parse argumentos
    if len(sys.argv) > 1:
        if sys.argv[1] == "--status":
            wd = KotharWatchdog()
            status = wd.get_status()
            if status:
                print(wd.monitor.get_status_text(status))
            else:
                print("Nenhum status disponível")
            sys.exit(0)
        elif sys.argv[1] == "--once":
            # Apenas uma verificação
            wd = KotharWatchdog()
            status = wd.monitor.get_status()
            print(wd.monitor.get_status_text(status))
            sys.exit(0)
        elif sys.argv[1] == "--cleanup":
            wd = KotharWatchdog()
            results = wd.process_manager.cleanup_cache()
            print(f"Limpeza concluída: {len(results['cleared'])} itens")
            sys.exit(0)

    # Iniciar watchdog
    watchdog = KotharWatchdog()
    watchdog.run()
