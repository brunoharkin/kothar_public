"""The temporary promotion workflow must fail without external side effects."""
from pathlib import Path
import subprocess
import yaml

WORKFLOW = Path(__file__).resolve().parents[2] / '.github/workflows/deploy.yml'


def load_workflow():
    # BaseLoader preserves the YAML 'on' key rather than treating it as YAML 1.1 bool.
    return yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)


def test_deployment_triggers_are_explicitly_blocked():
    workflow = load_workflow()
    assert set(workflow['on']) == {'push', 'workflow_dispatch'}
    assert set(workflow['on']['push']['branches']) == {'main', 'master'}
    assert workflow['permissions'] == {}
    assert set(workflow['jobs']) == {'production-blocked'}
    job = workflow['jobs']['production-blocked']
    assert 'if' not in job and 'continue-on-error' not in job
    assert 'environment' not in job and 'secrets' not in job
    assert len(job['steps']) == 1
    step = job['steps'][0]
    assert set(step) == {'name', 'shell', 'run'}
    assert step['shell'] == 'bash'
    # Restrict this containment job to messages and an unconditional refusal.
    lines = step['run'].strip().splitlines()
    assert all(line.strip().startswith('echo ') for line in lines[:-1])
    assert lines[-1].strip() == 'exit 1'
    assert '${{' not in step['run'] and '$(' not in step['run'] and '`' not in step['run']


def test_actual_blocking_command_fails_without_credentials(tmp_path):
    step = load_workflow()['jobs']['production-blocked']['steps'][0]
    result = subprocess.run(['bash', '-e', '-c', step['run']], cwd=tmp_path,
                            env={'PATH': '/usr/bin:/bin'}, capture_output=True, text=True)
    assert result.returncode == 1
    assert '::error::Deploy bloqueado' in result.stdout
    assert not list(tmp_path.iterdir())
