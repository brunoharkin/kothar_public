"""
LocalTokenLedger - Contador Local de Tokens
============================================

Inspirado em LocalTokenLedger.swift do Codenotch.

Este módulo implementa o contador local de tokens que:
1. Registra predições de tokens por instância e dia
2. Agrega totais para visualização
3. Mantém política de retenção (limpeza de dias antigos)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from typing import Optional
import json
import os
from pathlib import Path


@dataclass
class LocalPrediction:
    """
    Registro de uma única resposta com contagem de tokens.
    """
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    reasoning_tokens: int = 0
    draft_tokens: int = 0
    accepted_draft_tokens: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "draft_tokens": self.draft_tokens,
            "accepted_draft_tokens": self.accepted_draft_tokens,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LocalPrediction":
        """Reconstrói uma predição a partir de um dicionário."""
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            reasoning_tokens=data.get("reasoning_tokens", 0),
            draft_tokens=data.get("draft_tokens", 0),
            accepted_draft_tokens=data.get("accepted_draft_tokens", 0),
            timestamp=datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data else datetime.now(),
        )

    @classmethod
    def from_dict(cls, data: dict) -> "LocalPrediction":
        return cls(
            input_tokens=data.get("input_tokens"),
            output_tokens=data.get("output_tokens"),
            reasoning_tokens=data.get("reasoning_tokens", 0),
            draft_tokens=data.get("draft_tokens", 0),
            accepted_draft_tokens=data.get("accepted_draft_tokens", 0),
            timestamp=datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data else datetime.now(),
        )


@dataclass
class Totals:
    """Totais agregados de tokens."""
    requests: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    reasoning_tokens: int = 0
    draft_tokens: int = 0
    accepted_draft_tokens: int = 0

    def add(self, prediction: LocalPrediction) -> None:
        """Acumula uma predição aos totais."""
        self.requests += 1
        self.input_tokens += prediction.input_tokens or 0
        self.output_tokens += prediction.output_tokens or 0
        self.reasoning_tokens += prediction.reasoning_tokens or 0
        self.draft_tokens += prediction.draft_tokens or 0
        self.accepted_draft_tokens += prediction.accepted_draft_tokens or 0

    def __add__(self, other: Totals) -> Totals:
        return Totals(
            requests=self.requests + other.requests,
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            reasoning_tokens=self.reasoning_tokens + other.reasoning_tokens,
            draft_tokens=self.draft_tokens + other.draft_tokens,
            accepted_draft_tokens=self.accepted_draft_tokens + other.accepted_draft_tokens,
        )

    @property
    def total_tokens(self) -> int:
        """Total de tokens (input + output)."""
        return self.input_tokens + self.output_tokens

    @property
    def reasoning_share(self) -> float:
        """Fração do output gasta em raciocínio."""
        if self.output_tokens == 0:
            return 0.0
        return self.reasoning_tokens / self.output_tokens

    def to_dict(self) -> dict:
        return {
            "requests": self.requests,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "reasoning_tokens": self.reasoning_tokens,
            "draft_tokens": self.draft_tokens,
            "accepted_draft_tokens": self.accepted_draft_tokens,
            "reasoning_share": round(self.reasoning_share, 4),
        }


class LocalTokenLedger:
    """
    Contador local de tokens que agrega por instância e por dia.

    Inspirado em LocalTokenLedger.swift do Codenotch.

    Estrutura:
        days: {instance: {date: Totals}}

    Exemplo de uso:
        ledger = LocalTokenLedger()

        # Registrar uma resposta
        ledger.record(LocalPrediction(
            input_tokens=1000,
            output_tokens=500,
            reasoning_tokens=200,
        ))

        # Ver totais de hoje
        today = ledger.totals_today()
        print(f"Tokens hoje: {today.total_tokens}")

    Limpeza automática:
        - Dias com mais de 60 dias são removidos
        - Chama cleanup_old_days() para forçar limpeza
    """

    DEFAULT_RETENTION_DAYS = 60

    def __init__(
        self,
        storage_path: Optional[str] = None,
        retention_days: int = DEFAULT_RETENTION_DAYS,
    ):
        """
        Inicializa o ledger.

        Args:
            storage_path: Caminho para persistência
                          (default: ~/.kothar/token-usage/)
            retention_days: Dias para manter antes de limpar
        """
        if storage_path is None:
            storage_path = os.path.expanduser("~/.kothar/token-usage")

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days

        # Estrutura: {instance: {date: Totals}}
        self.days: dict[str, dict[str, Totals]] = {}

        # Carrega dados do disco
        self._load_from_disk()

        # Limpa dias antigos na inicialização
        self.cleanup_old_days()

    def _date_key(self, dt: datetime) -> str:
        """Retorna chave de data no formato YYYY-MM-DD."""
        return dt.strftime("%Y-%m-%d")

    def _instance_file(self, instance: str) -> Path:
        """Retorna caminho do arquivo para uma instância."""
        safe_name = instance.replace("/", "_").replace("\\", "_")
        return self.storage_path / f"{safe_name}.json"

    def record(
        self,
        prediction: LocalPrediction,
        instance: str = "default",
    ) -> None:
        """
        Registra uma predição no ledger.

        Args:
            prediction: Dados de tokens da resposta
            instance: Identificador da instância
        """
        if instance not in self.days:
            self.days[instance] = {}

        day_key = self._date_key(prediction.timestamp)

        if day_key not in self.days[instance]:
            self.days[instance][day_key] = Totals()

        self.days[instance][day_key].add(prediction)
        self._save_to_disk(instance)

    def totals_today(self, instance: str = "default") -> Totals:
        """
        Retorna totais do dia atual para uma instância.

        Args:
            instance: Identificador da instância

        Returns:
            Totais agregados do dia
        """
        today = self._date_key(datetime.now())
        return self.days.get(instance, {}).get(today, Totals())

    def totals_for_date(
        self,
        target_date: date,
        instance: str = "default",
    ) -> Totals:
        """Retorna totais para uma data específica."""
        date_key = target_date.strftime("%Y-%m-%d")
        return self.days.get(instance, {}).get(date_key, Totals())

    def totals_for_range(
        self,
        start_date: date,
        end_date: date,
        instance: str = "default",
    ) -> Totals:
        """Retorna totais para um intervalo de datas."""
        instance_days = self.days.get(instance, {})

        total = Totals()
        current = start_date

        while current <= end_date:
            date_key = current.strftime("%Y-%m-%d")
            if date_key in instance_days:
                total = total + instance_days[date_key]
            current += timedelta(days=1)

        return total

    def totals_all_time(self, instance: str = "default") -> Totals:
        """Retorna totais de todos os dias para uma instância."""
        instance_days = self.days.get(instance, {})
        if not instance_days:
            return Totals()

        total = Totals()
        for day_totals in instance_days.values():
            total = total + day_totals
        return total

    def all_instances(self) -> list[str]:
        """Retorna lista de todas as instâncias registradas."""
        return list(self.days.keys())

    def all_dates(self, instance: str = "default") -> list[str]:
        """Retorna lista de todas as datas para uma instância."""
        return sorted(
            self.days.get(instance, {}).keys(),
            reverse=True,
        )

    def cleanup_old_days(self, keep_days: Optional[int] = None) -> int:
        """
        Remove dias mais antigos que keep_days.

        Args:
            keep_days: Número de dias para manter (default: self.retention_days)

        Returns:
            Número de dias removidos
        """
        if keep_days is None:
            keep_days = self.retention_days

        cutoff = datetime.now() - timedelta(days=keep_days)
        cutoff_key = self._date_key(cutoff)

        removed = 0
        instances_to_remove = []

        for instance in list(self.days.keys()):
            old_days = [
                day_key for day_key in self.days[instance].keys()
                if day_key < cutoff_key
            ]
            for day_key in old_days:
                del self.days[instance][day_key]
                removed += 1

            if not self.days[instance]:
                instances_to_remove.append(instance)
            else:
                self._save_to_disk(instance)

        # Remove instâncias vazias
        for instance in instances_to_remove:
            del self.days[instance]
            # Remove arquivo do disco
            filepath = self._instance_file(instance)
            if filepath.exists():
                filepath.unlink()

        return removed

    def _save_to_disk(self, instance: str) -> None:
        """Salva dados de uma instância em disco."""
        filepath = self._instance_file(instance)
        instance_data = self.days.get(instance, {})

        data = {
            day_key: totals.to_dict()
            for day_key, totals in instance_data.items()
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    def _load_from_disk(self) -> None:
        """Carrega dados do disco para todas as instâncias."""
        if not self.storage_path.exists():
            return

        for filepath in self.storage_path.glob("*.json"):
            instance = filepath.stem
            try:
                with open(filepath) as f:
                    data = json.load(f)

                self.days[instance] = {}
                for day_key, totals_dict in data.items():
                    self.days[instance][day_key] = Totals(
                        requests=totals_dict.get("requests", 0),
                        input_tokens=totals_dict.get("input_tokens", 0),
                        output_tokens=totals_dict.get("output_tokens", 0),
                        reasoning_tokens=totals_dict.get("reasoning_tokens", 0),
                        draft_tokens=totals_dict.get("draft_tokens", 0),
                        accepted_draft_tokens=totals_dict.get("accepted_draft_tokens", 0),
                    )
            except (json.JSONDecodeError, IOError):
                # Ignora arquivos corrompidos
                pass

    def to_dict(self) -> dict:
        """Serializa o ledger para dicionário."""
        return {
            instance: {
                day_key: totals.to_dict()
                for day_key, totals in days.items()
            }
            for instance, days in self.days.items()
        }

    def summary(self, instance: str = "default") -> dict:
        """
        Retorna um resumo do uso para uma instância.

        Inclui totais hoje, últimos 7 dias, e todos os tempos.
        """
        now = datetime.now()
        today = now.date()
        week_ago = today - timedelta(days=7)

        return {
            "instance": instance,
            "today": self.totals_today(instance).to_dict(),
            "last_7_days": self.totals_for_range(week_ago, today, instance).to_dict(),
            "all_time": self.totals_all_time(instance).to_dict(),
            "dates_tracked": len(self.all_dates(instance)),
        }
