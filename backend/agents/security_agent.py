"""
=============================================================
 KOTHAR v4.0 — Agente de Segurança (Auditor Isolado)
 Engenheiro Kothar | Ugarit Digital
=============================================================
 Varre padrões de credenciais e registra a cobertura real.
 Não substitui autorização, testes de abuso ou gate de produção.
 Roda em contexto ISOLADO — não tem acesso ao histórico da sessão.
"""

import ast
import json
import re
from bisect import bisect_right
from pathlib import Path
from typing import Any

from backend.agents.base_agent import BaseAgent
from backend.core.logger import get_logger
from backend.trace.trace_recorder import trace_recorder

log = get_logger("agents.security")

# Padrões de segurança a verificar
PATTERNS = {
    "api_key_generic":    re.compile(r'(?i)["\']?(api[_-]?key|apikey)["\']?\s*[:=]\s*["\'][^"\']+["\']'),
    "aws_key":            re.compile(r'AKIA[0-9A-Z]{16}'),
    "private_key_header": re.compile(r'-----BEGIN (RSA |EC )?PRIVATE KEY-----'),
    "jwt_secret":         re.compile(r'(?i)["\']?(jwt[_-]?secret|secret[_-]?key)["\']?\s*[:=]\s*["\'][^"\']+["\']'),
    "password_hardcoded": re.compile(r'(?i)["\']?(password|passwd|pwd|senha)["\']?\s*[:=]\s*["\'][^"\']+["\']'),
    "token_hardcoded":    re.compile(r'(?i)["\']?(token|(?:access|refresh|session|auth|bearer)[_-]?token)["\']?\s*[:=]\s*["\'][^"\']+["\']'),
    "secret_hardcoded":   re.compile(r'(?i)["\']?(secret|client[_-]?secret|private[_-]?key|public[_-]?key|chave)["\']?\s*[:=]\s*["\'][^"\']+["\']'),
    "db_url_with_creds":  re.compile(
        r'''(?i)(?:postgres(?:ql)?|mysql|mongodb|rediss?)(?:\+[a-z0-9_-]+)?://'''
        r'''[^:/@\s"'`]*:(?P<password>[^@\s"'`]+)@'''
    ),
    "github_token":       re.compile(r'ghp_[a-zA-Z0-9]{36}'),
    "anthropic_key":      re.compile(r'sk-ant-[a-zA-Z0-9\-_]{40,}'),
    "openai_key":         re.compile(r'\bsk-(?:proj-|svcacct-)?[a-zA-Z0-9_\-]{40,}\b'),
}

# Os padrões públicos acima mantêm compatibilidade. A decisão de bloqueio usa
# uma única função, compartilhada pela pré-gravação e pela auditoria de arquivos.
_ASSIGNMENT_PATTERNS = {
    "api_key_generic", "jwt_secret", "password_hardcoded", "token_hardcoded", "secret_hardcoded",
}
_CREDENTIAL_FIELDS = {
    "api_key_generic": ("apikey",),
    "jwt_secret": ("jwtsecret", "secretkey"),
    "password_hardcoded": ("password", "passwd", "pwd", "senha"),
    "token_hardcoded": ("token", "accesstoken", "refreshtoken", "sessiontoken", "authtoken", "bearertoken"),
    "secret_hardcoded": ("secret", "clientsecret", "privatekey", "publickey", "chave"),
}
_FIELD_KEY_EXPRESSION = r'''(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[A-Za-z_$][\w$-]*)'''
_JSON_STRING = re.compile(r'"(?:\\.|[^"\\])*"')
_FIELD_ASSIGNMENT = re.compile(
    rf"(?<![\w$])(?P<key>{_FIELD_KEY_EXPRESSION})\s*"
    # A anotação opcional cobre `password: str = ...`, sem confundir
    # `password: str` ou `password: process.env.PASSWORD` com literais.
    r"(?::\s*[A-Za-z_][\w.\[\], |]*\s*=|:(?!=)|=(?!=))\s*"
)
_QUOTED_VALUE = re.compile(
    r"(?P<prefix>(?i:br|rb|fr|rf|r|u|b|f)?)(?P<quote>\"\"\"|'''|\"|'|`)"
    r"(?P<body>(?:\\[\s\S]|(?!(?P=quote))[^\\])*)(?P=quote)"
)
_NUMERIC_VALUE = re.compile(
    r"[+-]?(?:0[xX][0-9a-fA-F_]+|0[bB][01_]+|0[oO][0-7_]+|"
    r"(?:\d[\d_]*(?:\.[\d_]*)?|\.\d[\d_]*)(?:[eE][+-]?[\d_]+)?)(?:[jJnN])?"
    r"(?![\w.])(?=[ \t]*(?:$|[\r\n;,}\])]|\#|//))"
)
_ENV_ASSIGNMENT = re.compile(r"(?m)^\s*(?:export\s+)?(?P<key>[A-Z][A-Z0-9_]*)=(?P<value>[^\n]*)$")
_ENV_REFERENCE = re.compile(
    r"^(?:os\.(?:getenv\s*\(|environ(?:\s*\[|\.))|process\.env(?:\s*\[|\.)|"
    r"(?:getenv|env)\s*\(|\$\{[^}]+\}$|\$[A-Za-z_][A-Za-z0-9_]*$|\{\{.*\}\}$)"
)
_JS_TOKEN = re.compile(
    r'''\s*(?P<token>"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|'''
    r'''[A-Za-z_$][\w$]*|(?:\d[\w.]*)|'''
    r'''===|!==|==|!=|<=|>=|&&|\|\||\?\?|\?\.|[?.:\[\](),+*/%<>=!~-])'''
)


def _credential_pattern(key: str) -> str | None:
    """Reconhece nomes conhecidos, inclusive camelCase e prefixos de ambiente."""
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    parts = re.split(r"[\s_-]+", separated.casefold())
    candidates = {"".join(parts[index:]) for index in range(len(parts))}
    for pattern, fields in _CREDENTIAL_FIELDS.items():
        if candidates.intersection(fields):
            return pattern
    return None


def _decode_field_key(token: str) -> str:
    if token.startswith('"'):
        return json.loads(token)
    if token.startswith("'"):
        return ast.literal_eval(token)
    return token


def _reference_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _reference_name(node.value)
        return prefix + "." + node.attr if prefix else ""
    return ""


def _empty_literal(node: ast.AST) -> bool:
    return isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and not node.value


def _lookup_metadata(node: ast.AST) -> bool:
    """Chaves/índices escolhem um valor externo; não são a credencial retornada."""
    if isinstance(node, ast.Constant):
        return isinstance(node.value, (str, int))
    if isinstance(node, ast.IfExp):
        return _lookup_metadata(node.body) and _lookup_metadata(node.orelse)
    return _pure_dynamic_value(node)


def _safe_lookup_call(node: ast.Call) -> bool:
    """Permite loaders conhecidos; defaults literais nunca viram metadados."""
    name = _reference_name(node.func)
    named_loader = name in {"os.getenv", "getenv", "require_secret"} or name.endswith(".require_secret")
    mapping_lookup = (isinstance(node.func, ast.Attribute) and node.func.attr == "get"
                      and _pure_dynamic_value(node.func.value))
    if not (named_loader or mapping_lookup) or len(node.args) > 2:
        return False
    if any(isinstance(argument, ast.Starred) for argument in node.args):
        return False
    arguments = list(node.args)
    for keyword in node.keywords:
        if ((keyword.arg in {"key", "name"} and not arguments)
                or (keyword.arg in {"default", "value"} and len(arguments) == 1)):
            arguments.append(keyword.value)
        else:
            return False
    if not arguments or not _lookup_metadata(arguments[0]):
        return False
    if len(arguments) == 1:
        return True
    fallback = arguments[1]
    return ((isinstance(fallback, ast.Constant) and fallback.value is None)
            or _pure_dynamic_value(fallback))


def _pure_dynamic_value(node: ast.AST) -> bool:
    """Todos os ramos que retornam VALOR devem ser referências ou vazios.

    A presença de um nome em outro ramo não neutraliza um literal. Chamadas
    desconhecidas são rejeitadas: argumentos podem esconder defaults/senhas.
    """
    if _empty_literal(node) or isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Attribute):
        return _pure_dynamic_value(node.value)
    if isinstance(node, ast.Subscript):
        return _pure_dynamic_value(node.value) and _lookup_metadata(node.slice)
    if isinstance(node, ast.Call):
        return _safe_lookup_call(node)
    if isinstance(node, ast.IfExp):
        return _pure_dynamic_value(node.body) and _pure_dynamic_value(node.orelse)
    if isinstance(node, ast.BoolOp):
        return all(_pure_dynamic_value(value) for value in node.values)
    if isinstance(node, ast.BinOp):
        return _pure_dynamic_value(node.left) and _pure_dynamic_value(node.right)
    if isinstance(node, ast.JoinedStr):
        return all(_empty_literal(value) or (isinstance(value, ast.FormattedValue)
                   and _pure_dynamic_value(value.value)
                   and (value.format_spec is None or _pure_dynamic_value(value.format_spec)))
                   for value in node.values)
    return False


def _javascript_expression(expression: str) -> str:
    """Subconjunto léxico estrito; strings não participam da busca por nomes."""
    tokens = []
    position = 0
    while position < len(expression):
        match = _JS_TOKEN.match(expression, position)
        if not match:
            if expression[position:].isspace():
                break
            raise ValueError("unsupported_javascript_expression")
        tokens.append(match["token"])
        position = match.end()

    def translate(parts: list[str]) -> str:
        depth = 0
        conditional = -1
        nested_conditionals = 0
        for index, token in enumerate(parts):
            if token in {"(", "["}:
                depth += 1
            elif token in {")", "]"}:
                depth -= 1
            elif not depth and token == "?":
                if conditional == -1:
                    conditional = index
                else:
                    nested_conditionals += 1
            elif not depth and token == ":" and conditional != -1:
                if nested_conditionals:
                    nested_conditionals -= 1
                else:
                    condition = translate(parts[:conditional])
                    affirmative = translate(parts[conditional + 1:index])
                    negative = translate(parts[index + 1:])
                    return f"({affirmative} if {condition} else {negative})"
        translated = []
        replacements = {"||": "or", "??": "or", "&&": "and", "===": "==", "!==": "!=",
                        "true": "True", "false": "False", "null": "None", "undefined": "None", "?.": "."}
        index = 0
        while index < len(parts):
            token = parts[index]
            if token in {"(", "["}:
                closing = ")" if token == "(" else "]"
                nesting = 1
                end = index + 1
                while end < len(parts) and nesting:
                    if parts[end] == token:
                        nesting += 1
                    elif parts[end] == closing:
                        nesting -= 1
                    end += 1
                if nesting:
                    raise ValueError("unbalanced_javascript_expression")
                translated.append(token + translate(parts[index + 1:end - 1]) + closing)
                index = end
                continue
            if re.fullmatch(r"[A-Za-z_$][\w$]*", token):
                translated.append(replacements.get(token, token.replace("$", "_dollar_")))
            else:
                translated.append(replacements.get(token, token))
            index += 1
        return " ".join(translated)

    return translate(tokens)


def _expression_is_dynamic(expression: str, *, javascript: bool = False) -> bool:
    try:
        source = _javascript_expression(expression) if javascript else expression
        tree = ast.parse(source, mode="eval")
        return _pure_dynamic_value(tree.body)
    except (SyntaxError, ValueError, RecursionError):
        return False


def _template_has_static_content(body: str) -> bool:
    """Um template é dinâmico somente se todo conteúdo vier de interpolações."""
    position = 0
    while position < len(body):
        if not body.startswith("${", position):
            return True
        start = position + 2
        position = start
        depth = 1
        quote = ""
        while position < len(body) and depth:
            char = body[position]
            if char == "\\":
                position += 2
                continue
            if quote:
                if char == quote:
                    quote = ""
            elif char in {"'", '"', "`"}:
                quote = char
            elif char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
            position += 1
        if depth or not _expression_is_dynamic(body[start:position - 1].strip(), javascript=True):
            return True
    return False


def _quoted_has_static_content(literal: re.Match, *, body: str | None = None) -> bool:
    """Não confunde uma referência interpolada com uma senha literal."""
    value = literal["body"] if body is None else body
    if not value:
        return False
    if literal["quote"] == "`":
        return _template_has_static_content(value)
    if "f" not in literal["prefix"].casefold():
        return True
    source = literal["prefix"] + literal["quote"] + value + literal["quote"]
    try:
        tree = ast.parse(source, mode="eval").body
    except (SyntaxError, ValueError):
        return True
    if not isinstance(tree, ast.JoinedStr):
        return True
    return not _pure_dynamic_value(tree)


def find_credential_issues(content: str) -> list[dict[str, Any]]:
    """Retorna somente linha/padrão, nunca valores, trechos ou exceções com conteúdo.

    Strings atribuídas a campos sensíveis são bloqueadas sem mínimo de tamanho.
    Chaves JSON escapadas são decodificadas estritamente, inclusive em objetos
    aninhados. Expressões e referências de ambiente fora de strings não são
    literais. Linhas no formato dotenv (CHAVE=valor) são tratadas de forma
    conservadora, pois um valor sem aspas ali é configuração literal.
    """
    newlines = [match.start() for match in re.finditer("\n", content)]
    found: set[tuple[int, str]] = set()
    quoted_values = list(_QUOTED_VALUE.finditer(content))
    quoted_starts = [literal.start() for literal in quoted_values]

    def add(offset: int, pattern: str) -> None:
        found.add((bisect_right(newlines, offset) + 1, pattern))

    # Tokens e cabeçalhos reconhecíveis independem do nome da variável.
    intrinsic_patterns = [(name, pattern) for name, pattern in PATTERNS.items()
                          if name not in _ASSIGNMENT_PATTERNS]
    for pattern_name, pattern in intrinsic_patterns:
        for match in pattern.finditer(content):
            if pattern_name == "db_url_with_creds":
                index = bisect_right(quoted_starts, match.start()) - 1
                literal = quoted_values[index] if index >= 0 else None
                if (literal is not None and match.end() <= literal.end()
                        and not _quoted_has_static_content(literal, body=match["password"])):
                    continue
            add(match.start(), pattern_name)

    try:
        json.loads(content)
        is_json = True
    except (ValueError, RecursionError):
        is_json = False

    if is_json:
        # Normalizar somente JSON válido evita tanto escapes Unicode usados
        # para ocultar tokens conhecidos quanto avaliação de código/expressões.
        for match in _JSON_STRING.finditer(content):
            value = json.loads(match.group())
            for pattern_name, pattern in intrinsic_patterns:
                if pattern.search(value):
                    add(match.start(), pattern_name)

    decoder = json.JSONDecoder()
    for match in _FIELD_ASSIGNMENT.finditer(content):
        try:
            key = _decode_field_key(match["key"])
        except (ValueError, SyntaxError):
            continue
        pattern_name = _credential_pattern(key)
        if not pattern_name:
            continue
        literal = _QUOTED_VALUE.match(content, match.end())
        if ((literal and _quoted_has_static_content(literal))
                or (not literal and _NUMERIC_VALUE.match(content, match.end()))):
            add(match.start(), pattern_name)
        elif is_json:
            # Números também podem ser senhas. Objetos de schema, null e
            # booleanos não representam um valor de credencial aqui.
            try:
                value, _ = decoder.raw_decode(content, match.end())
            except ValueError:
                continue
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                add(match.start(), pattern_name)

    for match in _ENV_ASSIGNMENT.finditer(content):
        pattern_name = _credential_pattern(match["key"])
        value = match["value"].strip()
        if (pattern_name and value and not value.startswith("#") and not _QUOTED_VALUE.match(value)
                and not _ENV_REFERENCE.match(value)):
            add(match.start("key"), pattern_name)

    return [{"line": line, "pattern": pattern} for line, pattern in sorted(found)]

# Arquivos a ignorar na varredura
IGNORE_PATHS = {".env", ".env.example", ".gitignore", "example_skill.yaml", "__pycache__"}

# Extensões relevantes
SCAN_EXTENSIONS = {".py", ".ts", ".tsx", ".js", ".jsx", ".yaml", ".yml", ".json", ".sh", ".env", ".sql", ".toml", ".css", ".html"}


class SecurityAgent(BaseAgent):
    """
    Scanner de padrões de credenciais; outros controles exigem verificadores próprios.
    """

    @property
    def description(self) -> str:
        return "Scanner de credenciais com cobertura explícita; não certifica produção"

    async def execute(self, task: dict[str, Any]) -> dict[str, Any]:
        """Verifica padrões de credenciais com cobertura explícita dos arquivos pedidos."""
        if task.get("mode") == "dast" or task.get("scan_type") == "dast":
            return await self._run_nuclei_dast(str(task.get("target_url", "")))

        requested = task.get("files", [])
        if not isinstance(requested, list) or any(not isinstance(p, str) or not p for p in requested):
            return {"status": "blocked", "reason": "invalid_files", "coverage_complete": False}
        files_to_scan = list(requested)
        errors: list[dict[str, str]] = []
        ignored: list[dict[str, str]] = []
        all_issues: list[dict[str, Any]] = []
        scanned: list[str] = []
        root = Path(task.get("project_root") or Path.cwd()).resolve()

        scan_dir = task.get("scan_dir")
        if scan_dir:
            try:
                directory = Path(scan_dir).resolve(strict=True)
                if not directory.is_relative_to(root) or not directory.is_dir():
                    errors.append({"file": str(scan_dir), "reason": "invalid_scan_directory"})
                else:
                    files_to_scan.extend(self._collect_files(directory))
            except (OSError, ValueError, RuntimeError):
                errors.append({"file": str(scan_dir), "reason": "unreadable_directory"})

        # Copiar e deduplicar preserva a lista original e evita contagem dupla.
        files_to_scan = list(dict.fromkeys(files_to_scan))
        for filepath in files_to_scan:
            path = Path(filepath)
            if not path.is_absolute():
                path = root / path
            try:
                if not path.exists():
                    errors.append({"file": filepath, "reason": "missing_file"})
                    continue
                resolved = path.resolve(strict=True)
                if not resolved.is_relative_to(root):
                    errors.append({"file": filepath, "reason": "outside_project"})
                    continue
                if path.name in IGNORE_PATHS or path.suffix not in SCAN_EXTENSIONS:
                    ignored.append({"file": filepath, "reason": "unsupported_or_excluded_file"})
                    continue
                if not resolved.is_file():
                    errors.append({"file": filepath, "reason": "not_a_regular_file"})
                    continue
                all_issues.extend(self._scan_file(resolved))
                scanned.append(filepath)
            except (OSError, UnicodeError, ValueError, RuntimeError):
                errors.append({"file": filepath, "reason": "unreadable_file"})

        complete = bool(scanned) and not errors and not ignored and len(scanned) == len(files_to_scan)
        status = "failed" if errors or all_issues else ("passed" if complete else "blocked")
        report = self._format_report(all_issues, len(scanned))
        if not complete:
            report += f" Cobertura incompleta: {len(errors)} erro(s), {len(ignored)} exclusão(ões)."
        result = {
            "status": status,
            "agent": self.agent_name,
            "scope": "credential_patterns_only",
            "production_ready": False,
            "files_requested": len(files_to_scan),
            "files_scanned": len(scanned),
            "scanned_files": scanned,
            "ignored_files": ignored,
            "errors": errors,
            "coverage_complete": complete,
            "issues": all_issues,
            "report": report,
        }
        await trace_recorder.record(
            session_id=self.session_id,
            event_type="security_audit",
            agent_name=self.agent_name,
            content=report,
            tool_name="security_scanner",
            tool_output=result,
            is_error=status != "passed",
        )
        await self.record_decision(
            decision=f"Scanner de credenciais: {status}; {len(scanned)} arquivo(s) lido(s).",
            reasoning="Verificação limitada a padrões estáticos; não equivale a gate de produção.",
        )
        return result

    def _scan_file(self, path: Path) -> list[dict[str, Any]]:
        """Retorna só localização/padrão; erros de leitura sobem ao controle de cobertura."""
        content = path.read_text(encoding="utf-8")
        return [{"file": str(path), **issue} for issue in find_credential_issues(content)]

    def _collect_files(self, directory: Path) -> list[str]:
        """Percorre fontes suportadas e propaga erro de acesso ao chamador."""
        import os

        def on_error(error: OSError) -> None:
            raise error

        excluded_dirs = {".git", ".venv", "node_modules", "__pycache__", "dist", "build"}
        files = []
        for current, directories, filenames in os.walk(directory, onerror=on_error, followlinks=False):
            directories[:] = [d for d in directories if d not in excluded_dirs]
            for filename in filenames:
                path = Path(current) / filename
                if path.suffix in SCAN_EXTENSIONS:
                    files.append(str(path))
        return sorted(files)

    async def _run_nuclei_dast(self, target_url: str) -> dict[str, Any]:
        """DAST permanece indisponível até existir contrato de alvo/autorização verificável."""
        return {
            "status": "blocked",
            "reason": "dast_requires_authorized_executor",
            "scope": "dast_not_executed",
            "coverage_complete": False,
            "production_ready": False,
            "issues": [],
        }

    @staticmethod
    def _format_report(issues: list[dict], files_scanned: int) -> str:
        """Nunca inclui o conteúdo que pode conter a credencial detectada."""
        lines = [
            f"Scanner de padrões de credenciais: {files_scanned} arquivo(s) lido(s), "
            f"{len(issues)} ocorrência(s). Não comprova segurança de produção."
        ]
        for issue in issues[:20]:
            lines.append(f"  {issue['pattern']} — {issue['file']}:{issue['line']}")
        return "\n".join(lines)
