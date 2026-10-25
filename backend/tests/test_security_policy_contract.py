import copy
import json
from pathlib import Path

import pytest
from jsonschema import ValidationError, validate

ROOT = Path(__file__).resolve().parents[2]


def documents():
    return (json.loads((ROOT / 'configuracao/kothar-security-policy.json').read_text()),
            json.loads((ROOT / 'configuracao/kothar-security-policy.schema.json').read_text()))


def test_policy_is_fail_closed_and_references_real_skills():
    policy, schema = documents()
    validate(policy, schema)
    assert policy['fail_closed'] is True
    assert policy['default_environment'] == 'production'
    for skills in policy['surfaces'].values():
        for name in skills:
            assert (ROOT / '.agents/skills' / name / 'SKILL.md').is_file()


def test_policy_cannot_disable_fail_closed_or_add_unknown_fields():
    policy, schema = documents()
    disabled = copy.deepcopy(policy)
    disabled['fail_closed'] = False
    with pytest.raises(ValidationError):
        validate(disabled, schema)
    expanded = copy.deepcopy(policy)
    expanded['self_approved'] = True
    with pytest.raises(ValidationError):
        validate(expanded, schema)


def test_policy_is_wired_into_workspace_verifiers():
    for relative in ('scripts/sync-ides.sh', 'scripts/verify-kothar-agents.sh'):
        source = (ROOT / relative).read_text()
        assert 'verify-security-policy.py' in source
        assert 'sincronizar-politica-seguranca.py" --check' in source
