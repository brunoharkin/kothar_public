#!/usr/bin/env python3
"""
Compressor de Memória Kothar
Reduz históricos de sessão longos a summaries densos via API.
"""

import os
import json
import sys
from datetime import datetime
from typing import List, Dict, Any, Optional

def compress_session(input_file: str, output_file: str, max_messages: int = 50) -> bool:
    """
    Comprime um arquivo de sessão mantendo apenas as últimas N mensagens
    e gerando um summary das mensagens removidas.
    """
    try:
        with open(input_file, 'r') as f:
            lines = f.readlines()

        # Parse all messages
        messages = []
        for line in lines:
            try:
                messages.append(json.loads(line))
            except json.JSONDecodeError:
                continue

        if len(messages) <= max_messages:
            print(f"ℹ️ Sessão {input_file} já está dentro do limite ({len(messages)} msgs)")
            return False

        # Keep last N messages
        kept_messages = messages[-max_messages:]
        removed_messages = messages[:-max_messages]

        # Generate summary of removed messages
        summary = {
            "compressed_at": datetime.now().isoformat(),
            "original_count": len(messages),
            "removed_count": len(removed_messages),
            "kept_count": len(kept_messages),
            "first_message": removed_messages[0].get('timestamp', 'unknown') if removed_messages else None,
            "last_message": removed_messages[-1].get('timestamp', 'unknown') if removed_messages else None,
            "summary_generated": True
        }

        # Write compressed session
        with open(output_file, 'w') as f:
            for msg in kept_messages:
                f.write(json.dumps(msg) + '\n')

            # Add summary as last line
            summary_line = {
                "type": "session_compression_summary",
                "timestamp": datetime.now().isoformat(),
                "data": summary
            }
            f.write(json.dumps(summary_line) + '\n')

        print(f"✅ Sessão comprimida:")
        print(f"   Original: {len(messages)} mensagens")
        print(f"   Removidas: {len(removed_messages)} mensagens")
        print(f"   Mantidas: {len(kept_messages)} mensagens")

        return True

    except Exception as e:
        print(f"❌ Erro ao comprimir sessão: {e}")
        return False

def compress_all_sessions(memory_dir: str, max_messages: int = 50) -> Dict[str, bool]:
    """Comprime todas as sessões no diretório de memória."""
    results = {}

    if not os.path.exists(memory_dir):
        print(f"❌ Diretório não encontrado: {memory_dir}")
        return results

    jsonl_files = [f for f in os.listdir(memory_dir) if f.endswith('.jsonl')]

    for filename in jsonl_files:
        filepath = os.path.join(memory_dir, filename)
        backup_path = filepath + '.backup'

        # Create backup
        os.rename(filepath, backup_path)

        # Compress
        success = compress_session(backup_path, filepath, max_messages)
        results[filename] = success

        if success:
            # Remove backup
            os.remove(backup_path)

    return results

if __name__ == "__main__":
    memory_dir = os.path.expanduser("~/.claude/projects/-home-bruno-kothar")
    max_msgs = int(sys.argv[1]) if len(sys.argv) > 1 else 50

    print(f"🗜️ Compressor de Memória Kothar")
    print(f"   Diretório: {memory_dir}")
    print(f"   Limite: {max_msgs} mensagens por sessão\n")

    results = compress_all_sessions(memory_dir, max_msgs)

    print(f"\n📊 Resultado:")
    for filename, success in results.items():
        status = "✅" if success else "⏭️"
        print(f"   {status} {filename}")
