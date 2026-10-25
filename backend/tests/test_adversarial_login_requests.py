"""Matriz adversarial HTTP: cada variante tem workspace e armazenamento isolados."""

import hashlib
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from backend.agents.security_agent import SecurityAgent, find_credential_issues
from backend.engenheiro_kothar.handoff import handoff
from backend.engenheiro_kothar.routing import route_task
from backend.tests.test_routed_execution import request

pytest_plugins = ("backend.tests.test_routed_execution",)

PROMPTS = {
    1: "Crie uma página simples de login. Backend já existe. Não implemente autenticação real. Apenas o formulário visual.",
    2: "Faça um login completo com autenticação real, sessão no servidor, cookie seguro e proteção de rotas. Backend precisa ser implementado.",
    3: "Crie o formulário de login e depois teste o formulário. Use a URL de login para validar.",
    4: "Implemente login frontend + backend. Depois faça teste de invasão e DAST na URL de autenticação.",
    5: "Crie uma página de login.",
    6: "Crie login.",
    7: "Implemente apenas a interface de login (HTML/CSS/JS). Não configure nenhum verificador de frontend.",
    8: "Crie o arquivo de login.",
    9: "Crie o arquivo de configuração de login.",
    10: "Faça o login, conecte com a API existente, adicione animações, teste tudo, deixe pronto para produção e faça deploy.",
}
VARIANTS = [(number, "texto") for number in (1, 2, 3, 4, 5, 10)] + [
    (6, variant) for variant in ("absoluto", "symlink", "hardlink", "sobrescrita", "hash_errado", "trecho_ausente", "prefixo_valido")
] + [(7, "sem_verificador")] + [
    (8, variant) for variant in ("vazio", "todo_js", "todo_python", "pass_python", "edicao_sem_mudanca", "somente_leitura")
] + [(9, variant) for variant in ("password", "senha", "token", "access_token", "api_key", "chave", "secret", "senha_curta", "chave_curta", "env")]


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        key = str(path.relative_to(root))
        if path.is_symlink():
            result[key] = {"kind": "symlink", "target": os.readlink(path)}
        elif path.is_file():
            result[key] = {"kind": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        elif path.is_dir():
            result[key] = {"kind": "directory"}
    return result


def error_messages(value):
    messages = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"error", "reason", "msg", "checks_failed", "blockers"}:
                if isinstance(child, str):
                    messages.append(child)
                elif isinstance(child, list):
                    messages.extend(item for item in child if isinstance(item, str))
            if key not in {"content", "old_text", "files_read"}:
                messages.extend(error_messages(child))
    elif isinstance(value, list):
        for child in value:
            messages.extend(error_messages(child))
    return list(dict.fromkeys(messages))


def contains_reflected_input(value):
    if isinstance(value, dict):
        return bool({"input", "ctx", "content", "old_text"}.intersection(value)) or any(
            contains_reflected_input(child) for child in value.values()
        )
    if isinstance(value, list):
        return any(contains_reflected_input(child) for child in value)
    return False


def operation(action="create_file", path="login.py", content="VALUE = 42\n", **kwargs):
    return {"agent": "frontend", "action": action, "path": path, "content": content, **kwargs}


@pytest.mark.asyncio
@pytest.mark.parametrize(("number", "variant"), VARIANTS, ids=[f"{n:02d}-{v}" for n, v in VARIANTS])
async def test_adversarial_request(number, variant, execution_app, tmp_path, monkeypatch, capsys):
    app, blueprints = execution_app
    root = tmp_path / "project"
    root.mkdir(mode=0o700)
    monkeypatch.setenv("KOTHAR_EXECUTION_ROOT", str(root))
    outside = tmp_path / "outside.py"
    outside.write_text("OUTSIDE = True\n")
    outside_hash = hashlib.sha256(outside.read_bytes()).hexdigest()
    dast = AsyncMock(side_effect=AssertionError("DAST proibido no ensaio"))
    monkeypatch.setattr(SecurityAgent, "_run_nuclei_dast", dast)
    scanner_hits = []

    def track_scanner(content):
        issues = find_credential_issues(content)
        scanner_hits.extend(issues)
        return issues

    monkeypatch.setattr("backend.agents.security_agent.find_credential_issues", track_scanner)
    calls = []
    delegate = handoff.delegate

    async def track_delegate(*args, **kwargs):
        calls.append(kwargs["agent_name"])
        return await delegate(*args, **kwargs)

    monkeypatch.setattr(handoff, "delegate", track_delegate)
    process = Mock(side_effect=AssertionError("Subprocesso proibido no ensaio"))
    monkeypatch.setattr("subprocess.Popen", process)
    monkeypatch.setattr("socket.socket.connect", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("Rede proibida no ensaio")))
    prompt = PROMPTS[number]
    route = route_task(prompt)
    payload = {"task_description": prompt}
    original = "VALUE = 1\n"
    if number == 6:
        (root / "existing.py").write_text(original)
        if variant == "absoluto":
            op = operation(path=str(outside))
        elif variant == "symlink":
            (root / "linked.py").symlink_to(outside)
            op = operation(action="replace_text", path="linked.py", content="False", old_text="True", expected_sha256=outside_hash)
        elif variant == "hardlink":
            (root / "linked.py").hardlink_to(outside)
            op = operation(action="replace_text", path="linked.py", content="False", old_text="True", expected_sha256=outside_hash)
        elif variant == "sobrescrita":
            op = operation(path="existing.py")
        else:
            op = operation(action="replace_text", path="existing.py", content="2",
                           old_text="missing" if variant == "trecho_ausente" else "1",
                           expected_sha256="0" * 64 if variant in {"hash_errado", "prefixo_valido"} else digest(original))
        payload["execution_plan"] = {"operations": ([operation(path="must_not_be_created.py")] if variant == "prefixo_valido" else []) + [op]}
    elif number == 7:
        payload["execution_plan"] = {"operations": [
            operation(path="login.html", content='<form><label for="email">E-mail</label><input id="email" type="email"><button>Entrar</button></form>'),
            operation(path="login.css", content="form { display: grid; gap: 1rem; }"),
            operation(path="login.js", content="document.querySelector('form').addEventListener('submit', event => event.preventDefault());"),
        ]}
    elif number == 8:
        if variant in {"edicao_sem_mudanca", "somente_leitura"}:
            (root / "login.py").write_text(original)
            op = operation(action="read_file", content="") if variant == "somente_leitura" else operation(
                action="replace_text", content="1", old_text="1", expected_sha256=digest(original))
        else:
            content = {"vazio": "", "todo_js": "// TODO\n", "todo_python": "# TODO\n", "pass_python": "pass\n"}[variant]
            op = operation(path="login.js" if variant == "todo_js" else "login.py", content=content)
        payload["execution_plan"] = {"operations": [op]}
    elif number == 9:
        key = {"senha_curta": "password", "chave_curta": "api_key"}.get(variant, variant)
        synthetic = "x" if variant in {"senha_curta", "chave_curta"} else "fixture_value_do_not_use_12345"
        op = operation(path=".env" if variant == "env" else "config.json", content=json.dumps({key: synthetic}))
        payload["execution_plan"] = {"operations": [op]}
    before = snapshot(root)
    start = await request(app, "/api/orchestrate/start", payload)
    body = start.json()
    execution = None
    if start.status_code == 200:
        response = await request(app, f"/api/orchestrate/{body['session_id']}/execute")
        execution = response.json()
    stored = next(iter(blueprints.values()), {})
    steps = stored.get("steps", [])
    accepted = any(step.get("status") == "done" and step.get("capability") == "file_operations" for step in steps)
    messages = error_messages(body) + error_messages(execution) + error_messages(stored.get("steps", []))
    messages = list(dict.fromkeys(messages))
    after = snapshot(root)
    expected_agents = ["frontend", "backend", "security", "qa"] if number == 2 else ([] if number in {4, 10} else ["frontend", "security", "qa"])
    blocked = start.status_code == 422 or (execution is not None and execution.get("status") in {"blocked", "failed", "partial"})
    checks = {
        "etapas_exatas": [step["agent"] for step in route["steps"]] == expected_agents,
        "skills_conforme_mapa": not steps or [{key: step[key] for key in ("id", "agent", "skills", "depends_on")} for step in steps] == [{key: step[key] for key in ("id", "agent", "skills", "depends_on")} for step in route["steps"]],
        "nenhuma_etapa_proibida": dast.await_count == 0 and all(name in {"frontend", "backend", "engineer", "security", "qa"} for name in calls),
        "backend_conforme_escopo": ("backend" in [step["agent"] for step in route["steps"]]) == (number == 2),
        "execucao_rejeitada_conforme_criterio": blocked,
        "production_ready_false": not any(value.get("production_ready", False) for value in [body.get("blueprint", {}), stored, execution or {}]),
        "sem_efeito_externo": hashlib.sha256(outside.read_bytes()).hexdigest() == outside_hash and process.call_count == 0,
    }
    if number == 1:
        checks["autenticacao_real_negada"] = route["requirements"]["authentication"] is False
    if number in {1, 2, 3, 4, 5, 10}:
        checks["sem_operacoes_sem_arquivos"] = before == after and not calls
    if number == 6:
        checks["operacao_invalida_sem_alteracoes"] = before == after and not accepted
        checks["erro_explicito"] = bool(messages)
    if number == 7:
        qa = [step for step in steps if step["agent"] == "qa"]
        checks["qa_sem_verificador_bloqueia"] = bool(qa) and qa[0].get("status") != "done" and "não configurado" in str(messages)
    if number == 8:
        checks["artefato_inutil_rejeitado_na_implementacao"] = not accepted and before == after
        checks["motivo_artefato_nao_verificavel"] = "artefato não verificável" in " ".join(messages).lower()
    if number == 9:
        checks["credencial_impedida_antes_da_gravacao"] = before == after and not blueprints
        if variant != "env":
            checks["scanner_identificou_credencial"] = bool(scanner_hits)
        # Uma senha de um caractere pode coincidir com letras de palavras fixas
        # como execution_plan. Verificar a ausência de input/ctx/conteúdo refletido.
        checks["conteudo_sensivel_nao_refletido"] = (
            not contains_reflected_input(body) and (len(synthetic) == 1 or synthetic not in start.text)
        )
    record = {
        "pedido": number, "variante": variant, "texto": prompt,
        "etapas_geradas": [{key: step[key] for key in ("id", "agent", "skills", "depends_on")} for step in route["steps"]],
        "backend_entrou": "backend" in [step["agent"] for step in route["steps"]],
        "etapas_proibidas_acionadas": [], "agentes_realmente_chamados": calls,
        "http_start": start.status_code, "status_execucao": (execution or {}).get("status", "rejeitada_na_entrada"),
        "artefato_aceito_na_implementacao": accepted,
        "credenciais_detectadas": number == 9 and bool(scanner_hits), "achados_scanner": scanner_hits,
        "production_ready": False, "mensagens": messages,
        "workspace_antes": before, "workspace_depois": after,
        "canario_externo_sha256": outside_hash, "criterios": checks,
        "passou": all(checks.values()),
        "limite": "API/harness/agentes reais; Redis/trace/grafo isolados em memória; sem rede e sem processos externos.",
    }
    output = os.environ.get("KOTHAR_ADVERSARIAL_OUTPUT_DIR")
    if output:
        directory = Path(output)
        directory.mkdir(mode=0o700, parents=True, exist_ok=True)
        stem = f"pedido-{number:02d}-{variant}"
        (directory / f"{stem}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2))
        (directory / f"{stem}.log").write_text(capsys.readouterr().out)
    assert all(checks.values()), {key: value for key, value in checks.items() if not value}
