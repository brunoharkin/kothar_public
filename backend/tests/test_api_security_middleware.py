import hashlib
import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest
from fastapi import FastAPI

from backend.api.security import APISecurityMiddleware, COOKIE


class FakeStore:
    def __init__(self, data=None, count=1, fail=False):
        self.data = data
        self.count = count
        self.fail = fail
        self.keys = []

    async def get(self, key):
        if self.fail:
            raise ConnectionError('synthetic')
        self.keys.append(key)
        return self.data

    async def eval(self, script, number, key, ttl):
        if self.fail:
            raise ConnectionError('synthetic')
        assert number == 1 and ttl == 60
        return self.count


def session(username, password_hash, **changes):
    value = {
        'username': username,
        'csrfToken': 'b' * 64,
        'expiresAt': (datetime.now(timezone.utc) + timedelta(minutes=10)).isoformat(),
        'credentialVersion': hashlib.sha256((username + '\0' + password_hash).encode()).hexdigest(),
    }
    value.update(changes)
    return json.dumps(value)


def app(store):
    target = FastAPI()

    @target.get('/health')
    async def health():
        return {'status': 'ok'}

    @target.get('/private')
    async def private():
        return {'ok': True}

    @target.post('/private')
    async def mutate():
        return {'ok': True}

    target.add_middleware(APISecurityMiddleware, store=store)
    return target


async def request(target, method, path, **kwargs):
    cookies = kwargs.pop('cookies', None)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=target),
                                base_url='https://kothar.test', cookies=cookies) as client:
        return await client.request(method, path, **kwargs)


@pytest.mark.asyncio
async def test_missing_session_is_rejected_with_security_headers():
    response = await request(app(FakeStore()), 'GET', '/private')
    assert response.status_code == 401
    assert response.headers['cache-control'] == 'no-store'
    assert response.headers['x-frame-options'] == 'DENY'


@pytest.mark.asyncio
async def test_shared_session_and_csrf_contract(monkeypatch):
    username, password_hash, token = 'admin', 'aa:' + 'b' * 128, 'a' * 64
    monkeypatch.setenv('ADMIN_USERNAME', username)
    monkeypatch.setenv('ADMIN_PASSWORD_SCRYPT', password_hash)
    monkeypatch.setenv('CORS_ORIGIN', 'https://kothar.test')
    store = FakeStore(session(username, password_hash))
    target = app(store)
    cookies = {COOKIE: token}
    assert (await request(target, 'GET', '/private', cookies=cookies)).status_code == 200
    assert (await request(target, 'POST', '/private', cookies=cookies)).status_code == 403
    accepted = await request(target, 'POST', '/private', cookies=cookies,
                             headers={'Origin': 'https://kothar.test', 'X-CSRF-Token': 'b' * 64})
    assert accepted.status_code == 200
    assert store.keys[0].endswith(hashlib.sha256(token.encode()).hexdigest())


@pytest.mark.asyncio
@pytest.mark.parametrize('store, expected', [(FakeStore(fail=True), 503), (FakeStore(count=121), 429)])
async def test_store_failure_and_distributed_limit_fail_closed(monkeypatch, store, expected):
    username, password_hash = 'admin', 'aa:' + 'b' * 128
    monkeypatch.setenv('ADMIN_USERNAME', username)
    monkeypatch.setenv('ADMIN_PASSWORD_SCRYPT', password_hash)
    if not store.fail:
        store.data = session(username, password_hash)
    response = await request(app(store), 'GET', '/private', cookies={COOKIE: 'a' * 64})
    assert response.status_code == expected


@pytest.mark.asyncio
async def test_health_and_preflight_do_not_require_a_browser_session():
    target = app(FakeStore(fail=True))
    assert (await request(target, 'GET', '/health')).status_code == 200
    assert (await request(target, 'OPTIONS', '/private')).status_code != 401
