import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PRE = ROOT / 'hooks/agy-credential-scanner.py'
POST = ROOT / 'hooks/post-codegen-validate.py'


def run(script, payload, cwd=ROOT):
    return subprocess.run(
        ['python3', str(script)], input=payload, text=True, cwd=cwd,
        env={**os.environ, 'KOTHAR_PROJECT_DIR': str(cwd)},
        capture_output=True,
    )


def event(name='Write', **arguments):
    return json.dumps({'tool_name': name, 'tool_input': arguments})


def test_pre_hook_blocks_malformed_unknown_and_secret_writes():
    malformed = run(PRE, '{')
    assert json.loads(malformed.stdout)['decision'] == 'deny'
    missing = run(PRE, event('Write', file_path='safe.py'))
    assert json.loads(missing.stdout)['decision'] == 'deny'
    secret = 'sk-' + 'A' * 30
    blocked = run(PRE, event('apply_patch', patch='value = "' + secret + '"'))
    output = json.loads(blocked.stdout)
    assert output['decision'] == 'deny'
    assert secret not in blocked.stdout


def test_pre_hook_accepts_known_non_write_and_safe_write():
    assert json.loads(run(PRE, event('Read', file_path='x')).stdout)['decision'] == 'allow'
    assert json.loads(run(PRE, event('Write', file_path='x.py', content='value = None')).stdout)['decision'] == 'allow'


def test_post_hook_checks_final_file_and_root(tmp_path):
    safe = tmp_path / 'safe.py'
    safe.write_text('value = None')
    assert run(POST, event('Write', file_path='safe.py'), tmp_path).returncode == 0
    secret = 'sk-' + 'B' * 30
    safe.write_text('value = "' + secret + '"')
    blocked = run(POST, event('Write', file_path='safe.py'), tmp_path)
    assert blocked.returncode == 1
    assert secret not in blocked.stderr
    assert run(POST, event('Write', file_path='../outside.py'), tmp_path).returncode == 2


def test_post_hook_never_approves_parser_or_missing_file_failures(tmp_path):
    assert run(POST, '{', tmp_path).returncode == 2
    assert run(POST, event('Write', file_path='absent.py'), tmp_path).returncode == 2


def test_post_hook_manifest_points_to_fail_closed_validator():
    manifest = json.loads((ROOT / '.github/hooks/kothar-post-codegen-validate.json').read_text())
    command = manifest['kothar-post-codegen-validate']['PostToolUse'][0]['hooks'][0]['command']
    assert 'post-codegen-validate.py' in command
    assert 'post-codegen-validate.sh' not in command
