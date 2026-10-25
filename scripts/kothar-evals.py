#!/usr/bin/env python3
"""
Framework de Evals (Avaliação Contínua e Benchmark Semântico) do Kothar
Testa se o comportamento dos agentes adere aos contratos de qualidade, ausência de alucinação e segurança.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Execução a partir de qualquer diretório; o código importado vem do checkout deste script.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.servicos.evolucao.avaliacoes import (  # noqa: E402
    EvalCase,
    EvaluationError,
    OllamaEvaluationExecutor,
    evaluate_case,
    load_cases,
    run_evaluations,
)

CAMINHO_DATASET_TESTE = ROOT / "datasets/harness-whatsapp-avaliacao-v1.jsonl"

def avaliar_caso(caso: dict, executor=None, *, judge=None, artifact_root=None) -> dict:
    """Compatibilidade do nome público; executor ausente agora reprova configuração."""
    result = asyncio.run(evaluate_case(EvalCase.model_validate(caso), executor,
                                      judge=judge, artifact_root=artifact_root))
    return result.model_dump(mode="json")

def executar_evals(argv=None):
    parser = argparse.ArgumentParser(description="Avalia respostas executadas, sem criar dados ou resultados sintéticos.")
    parser.add_argument("--dataset", type=Path, default=CAMINHO_DATASET_TESTE)
    parser.add_argument("--provider", choices=["ollama"], required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", default="http://127.0.0.1:11434")
    parser.add_argument("--timeout", type=float, default=60)
    args = parser.parse_args(argv)
    try:
        cases = load_cases(args.dataset)
        executor = OllamaEvaluationExecutor(args.model, args.base_url, args.timeout)
        report = asyncio.run(run_evaluations(cases, executor, judge=executor.judge,
                                             timeout_seconds=args.timeout))
    except (EvaluationError, ValueError):
        # Exceções de validação podem incluir trechos de entrada. Não imprimir seus valores.
        print(json.dumps({"status": "blocked", "error_code": "evaluation_configuration_error"}))
        return 2
    # Relatório contém metadados e checks; nunca conteúdo do prompt/resposta.
    print(report.model_dump_json(indent=2))
    return 0 if report.all_passed and not report.contains_test_doubles else 1

if __name__ == "__main__":
    sys.exit(executar_evals())

