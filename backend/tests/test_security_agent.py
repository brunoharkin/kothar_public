"""Regressões do scanner: cobertura real, isolamento e saídas saneadas."""

import asyncio
import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from backend.agents.security_agent import PATTERNS, SecurityAgent, find_credential_issues
from backend.trace.trace_recorder import trace_recorder


@pytest.fixture
def scanner(monkeypatch):
    agent = SecurityAgent("security", "test-session")
    monkeypatch.setattr(agent, "search_skill", AsyncMock(return_value=[]))
    monkeypatch.setattr(agent, "record_decision", AsyncMock())
    monkeypatch.setattr(trace_recorder, "record", AsyncMock())
    return agent


def test_missing_file_is_not_approved(scanner, tmp_path):
    result = asyncio.run(scanner.execute({"files": [str(tmp_path / "missing.py")], "project_root": str(tmp_path)}))

    assert result["status"] == "failed"
    assert result["files_scanned"] == 0
    assert result["errors"][0]["reason"] == "missing_file"


def test_unreadable_file_is_not_approved(scanner, tmp_path, monkeypatch):
    target = tmp_path / "private.py"
    target.write_text("value = 1\n", encoding="utf-8")
    monkeypatch.setattr(Path, "read_text", lambda *args, **kwargs: (_ for _ in ()).throw(
        PermissionError("synthetic-read-denied")
    ))

    result = asyncio.run(scanner.execute({"files": [str(target)], "project_root": str(tmp_path)}))

    assert result["status"] == "failed"
    assert result["files_scanned"] == 0
    assert result["errors"][0]["reason"] == "unreadable_file"


def test_scan_has_real_coverage_and_does_not_mutate_task(scanner, tmp_path):
    target = tmp_path / "safe.py"
    target.write_text("value = 1\n", encoding="utf-8")
    files = ["safe.py"]
    result = asyncio.run(scanner.execute({"files": files, "scan_dir": str(tmp_path),
                                         "project_root": str(tmp_path)}))
    assert files == ["safe.py"]
    assert result["status"] == "passed"
    assert result["files_scanned"] > 0
    assert result["files_scanned"] == result["files_requested"]
    assert result["coverage_complete"] is True
    assert result["scope"] == "credential_patterns_only"
    assert result["production_ready"] is False
    assert "skills_applied" not in result


@pytest.mark.parametrize("filename", [None, "unhandled.bin", ".env"])
def test_zero_or_excluded_coverage_blocks_approval(scanner, tmp_path, filename):
    files = []
    if filename:
        target = tmp_path / filename
        target.write_text("fixture\n", encoding="utf-8")
        files.append(str(target))
    result = asyncio.run(scanner.execute({"files": files, "project_root": str(tmp_path)}))
    assert result["status"] == "blocked"
    assert result["coverage_complete"] is False
    assert result["files_scanned"] == 0


def test_symlink_outside_project_cannot_be_scanned(scanner, tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("value = 1\n", encoding="utf-8")
    target = project / "escape.py"
    target.symlink_to(outside)
    result = asyncio.run(scanner.execute({"files": [str(target)], "project_root": str(project)}))
    assert result["status"] == "failed"
    assert result["files_scanned"] == 0
    assert result["errors"][0]["reason"] == "outside_project"


def test_secret_is_never_copied_to_report_or_trace(scanner, tmp_path):
    synthetic = "dummy_credential_value_for_test"
    target = tmp_path / "unsafe.py"
    target.write_text(json.dumps({"password": synthetic}), encoding="utf-8")
    result = asyncio.run(scanner.execute({"files": [str(target)], "project_root": str(tmp_path)}))
    assert result["status"] == "failed"
    assert result["issues"]
    assert synthetic not in str(result)
    assert synthetic not in str(trace_recorder.record.await_args)
    assert "snippet" not in result["issues"][0]


def test_description_url_never_dispatches_dast(scanner, tmp_path, monkeypatch):
    dast = AsyncMock()
    monkeypatch.setattr(scanner, "_run_nuclei_dast", dast)
    asyncio.run(scanner.execute({"description": "leia https://example.invalid/", "files": [],
                                "project_root": str(tmp_path)}))
    dast.assert_not_awaited()


def test_dast_is_blocked_without_authorized_executor(scanner):
    result = asyncio.run(scanner.execute({"mode": "dast", "target_url": "https://example.invalid/"}))
    assert result["status"] == "blocked"
    assert result["reason"] == "dast_requires_authorized_executor"


@pytest.mark.parametrize("field", ["password", "api_key", "jwt_secret"])
def test_json_credential_fields_cannot_pass_scanner(scanner, tmp_path, field):
    target = tmp_path / "unsafe.json"
    synthetic = "fixture_credential_value_123456"
    target.write_text(json.dumps({field: synthetic}))
    result = asyncio.run(scanner.execute({"files": [str(target)], "project_root": str(tmp_path)}))
    assert result["status"] == "failed"
    assert result["issues"]
    assert synthetic not in str(result)


@pytest.mark.parametrize("field", [
    "password", "passwd", "pwd", "senha", "token", "access_token", "refresh_token", "session_token",
    "api_key", "chave", "secret", "client_secret", "private_key", "jwt_secret", "secret_key",
    "apiKey", "clientSecret", "accessToken", "DATABASE_PASSWORD", "OPENAI_API_KEY",
])
@pytest.mark.parametrize("length", [1, 2, 32])
def test_all_known_fields_reject_nonempty_json_literals_without_length_threshold(field, length):
    synthetic = chr(120) * length
    content = json.dumps({"configuration": [{field: synthetic}]}, indent=2)

    issues = find_credential_issues(content)

    assert issues
    assert all(set(issue) == {"line", "pattern"} for issue in issues)
    assert all(isinstance(issue["line"], int) and isinstance(issue["pattern"], str) for issue in issues)
    assert all(issue["line"] == 4 for issue in issues)
    assert synthetic not in json.dumps(issues)


@pytest.mark.parametrize("field", ["token", "access_token", "client_secret", "private_key", "senha"])
def test_json_escaped_keys_and_nested_objects_cannot_hide_credentials(field):
    escaped_key = '"' + "".join(f"\\u{ord(char):04x}" for char in field) + '"'
    synthetic = chr(120)
    content = '{"configuration": [{\n  ' + escaped_key + ": " + json.dumps(synthetic) + "}]}"

    issues = find_credential_issues(content)

    assert issues
    assert {issue["line"] for issue in issues} == {2}
    assert all(set(issue) == {"line", "pattern"} for issue in issues)


@pytest.mark.parametrize("template", [
    "{key} = {value}\n",                 # Python/TOML
    "{key}: str = {value}\n",            # Python annotated assignment
    "const {key} = {value};\n",          # JavaScript
    "const config = {{{key}: {value}}};",  # JavaScript object
    "{key}: {value}\n",                  # YAML
    "'{key}': {value}\n",                # YAML/Python quoted key
])
@pytest.mark.parametrize("quote", ['"', "'", "`"])
def test_quoted_credential_assignments_across_source_formats(template, quote):
    synthetic = chr(120)
    content = template.format(key="session_token", value=quote + synthetic + quote)

    assert find_credential_issues(content)


@pytest.mark.parametrize("key", ["PASSWORD", "ACCESS_TOKEN", "CLIENT_SECRET", "PRIVATE_KEY"])
def test_dotenv_literals_are_scanned_conservatively(key):
    content = key + "=" + chr(120) + "\n"

    assert find_credential_issues(content)


@pytest.mark.parametrize("content", [
    'password = os.getenv("APP_PASSWORD")\n',
    'password = os.environ["APP_PASSWORD"]\n',
    'const token = process.env.ACCESS_TOKEN;\n',
    'const config = {token: process.env.ACCESS_TOKEN};\n',
    'const {token} = configuration;\n',
    'token = configured_token\n',
    'password: str = Field(min_length=8)\n',
    'interface Login { password: string; token: string; }\n',
    'type Login = {password: string; token: string};\n',
    '{"properties":{"password":{"type":"string"}},"required":["password"]}',
    '{"token":null,"password":"","secret":false}',
    'ACCESS_TOKEN=process.env.ACCESS_TOKEN\n',
    'PASSWORD=os.getenv("APP_PASSWORD")\n',
    'PASSWORD=os.environ["APP_PASSWORD"]\n',
    'TOKEN=${ACCESS_TOKEN}\n',
    'TOKEN=$ACCESS_TOKEN\n',
    'TOKEN={{ environment.ACCESS_TOKEN }}\n',
    'TOKEN=\n',
    'PASSWORD= # configured in deployment\n',
])
def test_expressions_environment_references_and_type_schemas_are_not_literal_credentials(content):
    assert find_credential_issues(content) == []


def test_environment_reference_quoted_as_literal_is_rejected():
    content = " = ".join(("password", json.dumps("process.env.PASSWORD")))

    assert find_credential_issues(content)


def test_escaped_json_key_is_decoded_once():
    # Uma barra literal seguida por u não é a mesma chave que um escape Unicode.
    content = json.dumps({"\\u0074oken": chr(120)})

    assert find_credential_issues(content) == []


def test_escaped_intrinsic_token_in_json_is_detected_without_sensitive_field_name():
    synthetic = "ghp_" + "A" * 36
    escaped_value = '"' + "".join(f"\\u{ord(char):04x}" for char in synthetic) + '"'
    content = '{"configuration": {"value": ' + escaped_value + "}}"

    issues = find_credential_issues(content)

    assert any(issue["pattern"] == "github_token" for issue in issues)
    assert synthetic not in json.dumps(issues)


def test_file_and_content_scanners_share_identical_detection(scanner, tmp_path):
    content = json.dumps({"nested": {"refresh_token": chr(120)}}, indent=2)
    path = tmp_path / "configuration.json"
    path.write_text(content)

    expected = [{"file": str(path), **issue} for issue in find_credential_issues(content)]
    assert scanner._scan_file(path) == expected
    assert expected


def test_legacy_intrinsic_patterns_are_preserved():
    samples = [
        ("aws_key", "AKIA" + "A" * 16),
        ("private_key_header", "-----BEGIN " + "PRIVATE KEY-----"),
        ("db_url_with_creds", "://".join(("postgresql", chr(117) + ":" + chr(120) + "@host/database"))),
        ("github_token", "ghp_" + "A" * 36),
        ("anthropic_key", "sk-ant-" + "A" * 40),
        ("openai_key", "sk-proj-" + "A" * 40),
    ]
    for name, synthetic in samples:
        assert name in PATTERNS
        issues = find_credential_issues(synthetic)
        assert any(issue["pattern"] == name for issue in issues)
        assert synthetic not in json.dumps(issues)


@pytest.mark.parametrize("field", ["password", "senha", "token", "api_key", "chave", "secret"])
@pytest.mark.parametrize("number", ["7", "0", "-7", "3.14", "7e2", "0x7", "0b111"])
@pytest.mark.parametrize("template", ["{field} = {number}\n", "const {field} = {number};", "{field}: {number}\n"])
def test_numeric_source_credentials_are_rejected(field, number, template):
    content = template.format(field=field, number=number)

    assert find_credential_issues(content)


@pytest.mark.parametrize("expression", [
    "configured_password", "number7", "7 + configured_password", "7 * configured_password",
    "7 .toString()", "Number(configured_password)", "os.getenv('APP_PASSWORD')",
])
def test_numeric_prefixes_and_variables_are_not_mistaken_for_literal_values(expression):
    content = " = ".join(("password", expression)) + "\n"

    assert find_credential_issues(content) == []


@pytest.mark.parametrize("expression", [
    'f"{configured_password}"',
    'f"{os.environ[\'APP_PASSWORD\']}"',
    'f"{os.getenv(\'APP_PASSWORD\')}"',
    'f"{self.require_secret(\'APP_PASSWORD\', self.password)}"',
    'f"{first}{second}"',
    'fr"{configured_password}"',
    '`${process.env.ACCESS_TOKEN}`',
    '`${process.env["ACCESS_TOKEN"]}`',
    '`${configuration.token}`',
    '`${first}${second}`',
])
@pytest.mark.parametrize("field", ["password", "TOKEN"])
def test_purely_dynamic_interpolation_is_not_a_hardcoded_credential(expression, field):
    content = "=".join((field, expression)) + "\n"

    assert find_credential_issues(content) == []


@pytest.mark.parametrize("expression", [
    'f"literal"', 'f"{7}"', 'f"{\'literal\'}"', 'f"literal{configured_password}"',
    'f"{configured_password}literal"', 'f"{{literal}}"', '`literal`', '`${7}`',
    '`${"literal"}`', '`${true}`', '`literal${process.env.ACCESS_TOKEN}`',
    '`${process.env.ACCESS_TOKEN}literal`',
])
def test_static_content_inside_fstrings_or_templates_remains_blocked(expression):
    content = " = ".join(("password", expression)) + "\n"

    assert find_credential_issues(content)


@pytest.mark.parametrize("expression", [
    'f"{os.getenv(\'APP_PASSWORD\', \'x\')}"',
    'f"{\'x\' if True else configured_password}"',
    'f"{configured_password or \'x\'}"',
    'f"{configured_password and \'x\'}"',
    'f"{configuration.get(\'password\', \'x\')}"',
    'f"{unknown(\'x\')}"',
    'f"{configured_password:x<40}"',
    '`${"x" || ""}`',
    '`${process.env.ACCESS_TOKEN || "x"}`',
    '`${process.env.ACCESS_TOKEN && "x"}`',
    '`${process.env.ACCESS_TOKEN ?? "x"}`',
    '`${condition ? process.env.APP_VALUE : "x"}`',
    '`${condition ? "x" : process.env.ACCESS_TOKEN}`',
    '`${(condition ? process.env.APP_VALUE : "x")}`',
    '`${loader("x")}`',
])
def test_interpolation_with_literal_value_branch_is_blocked(expression):
    assert find_credential_issues(" = ".join(("password", expression)) + "\n")


@pytest.mark.parametrize("expression", [
    'f"{os.getenv(\'APP_PASSWORD\', None)}"',
    'f"{os.environ.get(\'APP_PASSWORD\')}"',
    'f"{os.getenv(\'APP_PASSWORD\', configured_password)}"',
    'f"{configured_password if condition else backup_password}"',
    'f"{configured_password or backup_password}"',
    '`${process.env.ACCESS_TOKEN || configuration.token}`',
    '`${process.env.ACCESS_TOKEN ?? configuration.token}`',
    '`${condition ? process.env.ACCESS_TOKEN : configuration.token}`',
    '`${(condition ? process.env.ACCESS_TOKEN : configuration.token)}`',
])
def test_interpolation_of_only_external_value_branches_is_allowed(expression):
    assert find_credential_issues(" = ".join(("password", expression)) + "\n") == []


def database_url(scheme, credential):
    return "://".join((scheme, "user:" + credential + "@host/database"))


@pytest.mark.parametrize("scheme", [
    "postgres", "postgresql", "postgresql+asyncpg", "mysql", "mysql+pymysql",
    "mongodb", "mongodb+srv", "redis", "rediss",
])
def test_literal_database_url_credentials_cannot_bypass_driver_prefixes(scheme):
    content = "url = " + json.dumps(database_url(scheme, chr(120)))

    assert any(issue["pattern"] == "db_url_with_creds" for issue in find_credential_issues(content))


@pytest.mark.parametrize("credential,quote,prefix", [
    ("{password}", '"', "f"),
    ("{self.password}", '"', "f"),
    ("${process.env.PASSWORD}", "`", ""),
    ('${process.env["PASSWORD"]}', "`", ""),
])
def test_purely_interpolated_database_password_is_not_a_literal(credential, quote, prefix):
    content = "url = " + prefix + quote + database_url("postgresql", credential) + quote

    assert find_credential_issues(content) == []


@pytest.mark.parametrize("credential,quote,prefix", [
    ("{password}", '"', ""),
    ("literal{password}", '"', "f"),
    ("{7}", '"', "f"),
    ("${7}", "`", ""),
    ("literal${process.env.PASSWORD}", "`", ""),
])
def test_static_password_components_in_database_interpolation_remain_blocked(credential, quote, prefix):
    content = "url = " + prefix + quote + database_url("postgresql", credential) + quote

    assert any(issue["pattern"] == "db_url_with_creds" for issue in find_credential_issues(content))


@pytest.mark.parametrize("separator", ['"\n f"', '" + "', "\n"])
def test_database_detector_never_crosses_lines_or_quoted_segments(separator):
    first, second = database_url("postgresql", "{password}").split("@")
    content = 'url = f"' + first + separator + "@" + second + '"'

    assert find_credential_issues(content) == []


def test_real_configuration_dsn_construction_is_not_a_literal_credential():
    path = Path(__file__).resolve().parents[1] / "core" / "config.py"

    assert find_credential_issues(path.read_text()) == []
