"""Operações revisáveis usadas pelo executor de tarefas, sem shell livre."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class FileOperation(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    agent: Literal["frontend", "backend", "engineer"]
    action: Literal["read_file", "create_file", "replace_text"]
    path: str = Field(min_length=1, max_length=500)
    content: str = Field(default="", max_length=100_000)
    old_text: str = Field(default="", max_length=100_000)
    expected_sha256: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def require_edit_precondition(self):
        from backend.core.workspace_files import check_content, relative_parts

        relative_parts(self.path)
        check_content(self.content)
        check_content(self.old_text)
        if self.action == "replace_text" and (not self.old_text or not self.expected_sha256):
            raise ValueError("Edição exige trecho original e SHA-256 do arquivo revisado.")
        if self.action != "replace_text" and (self.old_text or self.expected_sha256):
            raise ValueError("Precondições de edição só se aplicam a replace_text.")
        if self.action == "read_file" and self.content:
            raise ValueError("Leitura não recebe conteúdo para escrita.")
        return self


class TaskExecutionPlan(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    operations: list[FileOperation] = Field(default_factory=list, max_length=50)
    files: list[str] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def validate_scan_paths(self):
        from backend.core.workspace_files import relative_parts

        for path in self.files:
            relative_parts(path)
        return self
