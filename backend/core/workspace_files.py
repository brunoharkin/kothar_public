"""Acesso restrito ao workspace configurado pelo operador do servidor."""

import ast
import hashlib
import os
import re
import stat
import uuid
from contextlib import contextmanager, suppress
from pathlib import Path, PurePosixPath

MAX_FILE_BYTES = 400_000
EXTENSIONS = {".py", ".js", ".jsx", ".ts", ".tsx", ".css", ".html", ".json", ".sql", ".toml", ".yaml", ".yml"}
PROTECTED = {"AGENTS.md", "CLAUDE.md", "GEMINI.md", "SKILL.md", "node_modules", "__pycache__", "venv"}


class WorkspaceError(ValueError):
    """Erro seguro para resposta ao cliente, sem conteúdo ou caminho do host."""


def configured_workspace() -> Path:
    configured = os.environ.get("KOTHAR_EXECUTION_ROOT", "")
    if not configured:
        raise WorkspaceError("Workspace de execução não configurado pelo servidor.")
    root = Path(configured)
    if not root.is_absolute() or root.is_symlink():
        raise WorkspaceError("Workspace de execução inválido.")
    try:
        root = root.resolve(strict=True)
        if not root.is_dir():
            raise OSError
    except OSError as exc:
        raise WorkspaceError("Workspace de execução indisponível.") from exc
    return root


def relative_parts(path: str) -> tuple[str, ...]:
    if not isinstance(path, str) or not path or "\\" in path or "\x00" in path:
        raise WorkspaceError("Caminho de operação inválido.")
    parts = path.split("/")
    if any(not p or p.startswith(".") or p in PROTECTED for p in parts):
        raise WorkspaceError("Caminho protegido ou fora do escopo.")
    if PurePosixPath(path).is_absolute() or Path(parts[-1]).suffix not in EXTENSIONS:
        raise WorkspaceError("Tipo de arquivo não permitido para execução.")
    return tuple(parts)


@contextmanager
def _parent(root: Path, path: str, *, create: bool = False):
    parts = relative_parts(path)
    descriptors = []
    try:
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        descriptors.append(directory)
        for part in parts[:-1]:
            try:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, mode=0o700, dir_fd=directory)
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            descriptors.append(child)
            directory = child
        yield directory, parts[-1]
    except OSError as exc:
        raise WorkspaceError("Arquivo indisponível, existente ou caminho inseguro.") from exc
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _read(descriptor: int) -> tuple[str, os.stat_result]:
    info = os.fstat(descriptor)
    if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > MAX_FILE_BYTES:
        raise WorkspaceError("Arquivo não regular, compartilhado ou acima do limite.")
    with os.fdopen(os.dup(descriptor), "rb") as stream:
        raw = stream.read(MAX_FILE_BYTES + 1)
    if len(raw) > MAX_FILE_BYTES:
        raise WorkspaceError("Arquivo acima do limite.")
    try:
        return raw.decode("utf-8"), info
    except UnicodeError as exc:
        raise WorkspaceError("Arquivo não é texto UTF-8.") from exc


def check_content(content: str) -> None:
    # Importação tardia evita dependência de infraestrutura ao carregar contratos.
    from backend.agents.security_agent import find_credential_issues

    if len(content.encode("utf-8")) > MAX_FILE_BYTES:
        raise WorkspaceError("Conteúdo acima do limite.")
    if find_credential_issues(content):
        raise WorkspaceError("Conteúdo bloqueado pela verificação de credenciais.")


def check_artifact(content: str, path: str, *, previous: str | None = None) -> None:
    """Exige conteúdo concreto; sintaxe e comportamento têm verificadores próprios."""
    if previous is not None and content == previous:
        raise WorkspaceError("Artefato não verificável: edição sem alteração de conteúdo.")
    without_blocks = re.sub(r"/\*.*?\*/|<!--.*?-->", "", content, flags=re.DOTALL)
    without_comments = re.sub(r"(?m)^\s*(?://|#).*?$", "", without_blocks).strip()
    if not without_comments:
        raise WorkspaceError("Artefato não verificável: conteúdo vazio ou apenas comentários.")
    if Path(path).suffix == ".py":
        try:
            tree = ast.parse(content)
        except (SyntaxError, ValueError):
            return  # O QA reprova sintaxe inválida; não executar o código.

        def useful(node):
            if isinstance(node, (ast.Pass, ast.Break, ast.Continue, ast.Global, ast.Nonlocal)) or (
                isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
            ):
                return False
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                return False
            if isinstance(node, ast.Raise):
                exception = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
                if isinstance(exception, ast.Name) and exception.id == "NotImplementedError":
                    return False
                if isinstance(exception, ast.Attribute) and exception.attr == "NotImplementedError":
                    return False
            if isinstance(node, ast.Return) and (
                node.value is None or isinstance(node.value, ast.Constant) and node.value.value in (None, Ellipsis)
                or isinstance(node.value, ast.Name) and node.value.id == "NotImplemented"
            ):
                return False
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return any(useful(child) for child in node.body)
            if isinstance(node, ast.ClassDef):
                return any(useful(child) for child in node.body)
            if isinstance(node, (ast.If, ast.For, ast.AsyncFor, ast.While)):
                return any(useful(child) for child in [*node.body, *node.orelse])
            if isinstance(node, (ast.With, ast.AsyncWith)):
                return any(useful(child) for child in node.body)
            if isinstance(node, (ast.Try, ast.TryStar)):
                children = [*node.body, *node.orelse, *node.finalbody,
                            *(child for handler in node.handlers for child in handler.body)]
                return any(useful(child) for child in children)
            if isinstance(node, ast.Match):
                return any(useful(child) for case in node.cases for child in case.body)
            return True

        if not any(useful(node) for node in tree.body):
            raise WorkspaceError("Artefato não verificável: arquivo contém somente placeholder.")
        if previous is not None:
            try:
                unchanged = ast.dump(ast.parse(previous)) == ast.dump(tree)
            except (SyntaxError, ValueError):
                unchanged = False
            if unchanged:
                raise WorkspaceError("Artefato não verificável: edição sem alteração estrutural.")


def read_workspace_file(root: Path, path: str) -> str:
    with _parent(root, path) as (parent, name):
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            content, _ = _read(descriptor)
        finally:
            os.close(descriptor)
    check_content(content)
    return content


def create_workspace_file(root: Path, path: str, content: str) -> str:
    check_content(content)
    check_artifact(content, path)
    with _parent(root, path, create=True) as (parent, name):
        descriptor = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             0o600, dir_fd=parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        except BaseException:
            os.unlink(name, dir_fd=parent)
            raise
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def replace_workspace_text(root: Path, path: str, old: str, new: str, digest: str) -> str:
    with _parent(root, path) as (parent, name):
        descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        try:
            original, info = _read(descriptor)
        finally:
            os.close(descriptor)
        if hashlib.sha256(original.encode("utf-8")).hexdigest() != digest:
            raise WorkspaceError("Arquivo mudou desde a revisão; edição bloqueada.")
        if not old or original.count(old) != 1:
            raise WorkspaceError("Trecho original deve ocorrer exatamente uma vez.")
        updated = original.replace(old, new, 1)
        check_content(updated)
        check_artifact(updated, path, previous=original)
        temporary = f".kothar-edit-{uuid.uuid4().hex}"
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                             stat.S_IMODE(info.st_mode) & 0o700, dir_fd=parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
                stream.write(updated)
                stream.flush()
                os.fsync(stream.fileno())
            current = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if (current.st_dev, current.st_ino, current.st_mtime_ns, current.st_size) != (
                info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size
            ):
                raise WorkspaceError("Arquivo mudou durante a edição; operação bloqueada.")
            os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        finally:
            with suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=parent)
    return hashlib.sha256(updated.encode("utf-8")).hexdigest()
