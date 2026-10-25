"""Restrict operational telemetry to explicitly safe scalars, before serialization."""
import re
from typing import Any

# User text, tool arguments/results and exceptions are deliberately absent.
SAFE_FIELDS = frozenset('event level logger timestamp environment kothar_version session_id agent agent_name event_type seq tool tool_name status duration_ms tokens_used tokens_total tokens_input tokens_output tokens_in tokens_out cost_usd step_id total_steps completed_steps failed_steps skipped_steps total_duration_ms retries attempt error_type model files_scanned files_requested coverage_complete skills_found n_results count action failures threshold recovered chars tokens_est thinking_length_chars thinking_length_tokens_est'.split())
SAFE_LABEL = re.compile(r'^[\w .:/@+-]{0,128}$', re.UNICODE)
REDACTED = '[REDACTED]'


def safe_metadata(value: Any) -> dict:
    if not isinstance(value, dict):
        return {}
    result = {}
    for key, item in value.items():
        if key not in SAFE_FIELDS:
            continue
        if item is None or isinstance(item, (bool, int, float)):
            result[key] = item
        elif key == 'session_id' and isinstance(item, str) and re.fullmatch(r'[0-9a-fA-F-]{36}', item):
            result[key] = item
        elif key in {'status', 'action', 'level'} and isinstance(item, str) and item in {'active', 'started', 'completed', 'done', 'passed', 'failed', 'blocked', 'error', 'skipped', 'opened', 'closed', 'half_open', 'info', 'warning', 'debug'}:
            result[key] = item
    return result


def redact_log(logger, method_name, event_dict):
    """Keep fixed operational fields; omit arbitrary messages and exception payloads."""
    result = safe_metadata(event_dict)
    # Dynamic event strings may contain user input/secrets; preserve only static origin.
    result['event'] = 'operational_event'
    return result
