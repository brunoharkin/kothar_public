"""Regressions for production exposure controls; not a live TLS/firewall audit."""
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_published_ports_are_loopback_only():
    services = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())['services']
    for name, service in services.items():
        for port in service.get('ports', []):
            assert str(port).startswith('127.0.0.1:'), name


def test_no_credential_defaults_or_debug_reload():
    text = (ROOT / 'docker-compose.yml').read_text()
    for variable in ('POSTGRES_PASSWORD', 'REDIS_PASSWORD', 'NEO4J_PASSWORD'):
        assert '${' + variable + ':?' in text
        assert '${' + variable + ':-' not in text
    assert '--reload' not in text
    assert '- --no-auth\n' not in text


def test_internal_integrations_are_not_browser_public():
    services = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())['services']
    assert services['kothar_scrapling_mcp']['profiles'] == ['scrapling']
    assert not services['kothar_scrapling_mcp'].get('ports')
    assert services['kothar_chromadb']['environment']['CHROMA_SERVER_CORS_ALLOW_ORIGINS'] == '[]'


def test_auth_state_cannot_be_evicted_and_is_shared_by_both_apis():
    assert 'maxmemory-policy noeviction' in (ROOT / 'infra/redis/redis.conf').read_text()
    services = yaml.safe_load((ROOT / 'docker-compose.yml').read_text())['services']
    for name in ('kothar_harness_api', 'kothar_api'):
        environment = '\n'.join(services[name]['environment'])
        assert 'AUTH_REDIS_URL=' in environment
        assert 'ADMIN_USERNAME=' in environment
        assert 'ADMIN_PASSWORD_SCRYPT=' in environment
        assert 'CORS_ORIGIN=' in environment


def test_browser_edge_has_restrictive_headers_and_no_metrics_proxy():
    text = (ROOT / 'frontend/nginx.conf').read_text()
    for header in ('Strict-Transport-Security', 'X-Content-Type-Options',
                   'X-Frame-Options', 'Referrer-Policy', 'Content-Security-Policy'):
        assert 'add_header ' + header in text
    assert "connect-src 'self'" in text
    assert "script-src 'self'" in text
    assert 'proxy_pass http://kothar_api:8080/metrics' not in text
    assert 'access_log off;' in text


def test_python_api_is_non_root_and_source_mounts_are_read_only():
    dockerfile = (ROOT / 'backend/Dockerfile').read_text()
    compose = (ROOT / 'docker-compose.yml').read_text()
    assert 'USER kothar' in dockerfile
    assert 'install.sh | bash' not in dockerfile
    assert './backend:/app/backend:ro' in compose
    assert './scripts:/app/scripts:ro' in compose
    assert 'ENVIRONMENT=production' in compose
    assert 'no-new-privileges:true' in compose


def test_detailed_health_is_not_public_at_browser_edge():
    nginx = (ROOT / 'frontend/nginx.conf').read_text()
    security = (ROOT / 'backend/api/security.py').read_text()
    assert "'/health/detailed'" not in security
    assert 'location /health/' in nginx
