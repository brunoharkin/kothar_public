"""Normalize supported hook event shapes without treating malformed input as approval."""
from dataclasses import dataclass
from typing import Any


WRITE_TOOLS = {
    "write", "edit", "multiedit", "apply_patch", "write_to_file",
    "replace_file_content", "create_file", "str_replace_editor",
}


@dataclass(frozen=True)
class ToolEvent:
    name: str
    arguments: dict[str, Any]

    @property
    def is_write(self) -> bool:
        return self.name.lower() in WRITE_TOOLS

    def content(self) -> str | None:
        for key in ("CodeContent", "ReplacementContent", "content", "newContent",
                    "text", "patch", "input"):
            value = self.arguments.get(key)
            if isinstance(value, str):
                return value
        return None

    def path(self) -> str | None:
        for key in ("file_path", "path", "FilePath", "TargetFile", "target"):
            value = self.arguments.get(key)
            if isinstance(value, str) and value:
                return value
        return None


def normalize(payload: Any) -> ToolEvent:
    if not isinstance(payload, dict):
        raise ValueError("evento deve ser objeto")
    candidates = [
        (payload.get("tool_name"), payload.get("tool_input")),
        (payload.get("tool"), payload.get("arguments")),
        (payload.get("name"), payload.get("input")),
    ]
    tool_call = payload.get("toolCall")
    if isinstance(tool_call, dict):
        candidates.append((tool_call.get("name"), tool_call.get("args")))
    for name, arguments in candidates:
        if isinstance(name, str) and name and isinstance(arguments, dict):
            return ToolEvent(name=name, arguments=arguments)
    raise ValueError("contrato de ferramenta ausente")
