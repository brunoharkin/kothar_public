import re

file_path = "/home/bruno/kothar/backend/core/tools.py"
with open(file_path, "r") as f:
    content = f.read()

# Fix tool_search_code default base_dir
content = content.replace(
    'def tool_search_code(query: str, glob: str = "*.py", base_dir: str = "/home/bruno/kothar") -> Dict:',
    'def tool_search_code(query: str, glob: str = "*.py", base_dir: str = "/home/bruno/tracing") -> Dict:'
)
content = content.replace(
    'def tool_search_code(query: str, glob: str = "*.ts", base_dir: str = "/home/bruno/kothar") -> Dict:', # Just in case it was changed
    'def tool_search_code(query: str, glob: str = "*.py", base_dir: str = "/home/bruno/tracing") -> Dict:'
)

# Fix TOOLS_SCHEMA base_dir description and default
content = content.replace(
    '"description": "Diretório base (padrão: /home/bruno/kothar)",\n                        "default": "/home/bruno/kothar",',
    '"description": "Diretório base (padrão: /home/bruno/tracing)",\n                        "default": "/home/bruno/tracing",'
)

with open(file_path, "w") as f:
    f.write(content)

print("Patch applied to tools.py")
