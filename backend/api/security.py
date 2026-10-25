"""Redis-backed authentication for the Python API; shared with harness-api."""
import hashlib
import hmac
import json
import os
import re
from datetime import datetime, timezone

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

COOKIE = '__Host-kothar_session'
TOKEN = re.compile(r'^[a-f0-9]{64}$')
LIMIT_SCRIPT = """
local n=redis.call('INCR',KEYS[1])
if n==1 then redis.call('EXPIRE',KEYS[1],ARGV[1]) end
return n
"""


class APISecurityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, store=None):
        super().__init__(app)
        self.store = store

    async def redis(self):
        if self.store is not None:
            return self.store
        import redis.asyncio as redis
        url = os.environ.get('AUTH_REDIS_URL') or os.environ.get('REDIS_URL')
        if not url:
            raise RuntimeError('Authentication store is required')
        self.store = redis.from_url(url, decode_responses=True)
        return self.store

    async def dispatch(self, request, call_next):
        def deny(code, message):
            return JSONResponse(
                {'error': message}, status_code=code,
                headers={
                    'Cache-Control': 'no-store',
                    'X-Content-Type-Options': 'nosniff',
                    'X-Frame-Options': 'DENY',
                    'Referrer-Policy': 'no-referrer',
                },
            )

        if request.method == 'OPTIONS' or request.url.path in {'/health', '/health/'}:
            response = await call_next(request)
            response.headers['Cache-Control'] = 'no-store'
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['Referrer-Policy'] = 'no-referrer'
            return response

        token = request.cookies.get(COOKIE, '')
        if not TOKEN.fullmatch(token):
            return deny(401, 'Autenticação necessária')
        try:
            store = await self.redis()
            data = await store.get('kothar:auth:session:' + hashlib.sha256(token.encode()).hexdigest())
            if not data:
                return deny(401, 'Sessão inválida')
            session = json.loads(data)
            username = os.environ.get('ADMIN_USERNAME', '')
            password_hash = os.environ.get('ADMIN_PASSWORD_SCRYPT', '')
            if not username or not password_hash:
                return deny(503, 'Autenticação indisponível')
            version = hashlib.sha256((username + '\0' + password_hash).encode()).hexdigest()
            expiry = datetime.fromisoformat(session['expiresAt'].replace('Z', '+00:00'))
            stored_version = session.get('credentialVersion', '')
            if (expiry.tzinfo is None or expiry <= datetime.now(timezone.utc)
                    or not isinstance(stored_version, str)
                    or not hmac.compare_digest(stored_version, version)
                    or session.get('username') != username):
                return deny(401, 'Sessão inválida')
            if request.method not in {'GET', 'HEAD', 'OPTIONS'}:
                origins = {x.strip() for x in os.environ.get('CORS_ORIGIN', '').split(',') if x.strip()}
                csrf = request.headers.get('x-csrf-token', '')
                expected = session.get('csrfToken', '')
                if (request.headers.get('origin') not in origins
                        or not isinstance(expected, str)
                        or not expected
                        or not hmac.compare_digest(csrf, expected)):
                    return deny(403, 'Requisição não autorizada')
            # Shared limit survives replica/restart. No forwarding header is trusted.
            count = await store.eval(LIMIT_SCRIPT, 1, 'kothar:api:limit:' + hashlib.sha256(token.encode()).hexdigest(), 60)
            if int(count) > 120:
                return deny(429, 'Limite de requisições atingido')
        except Exception:
            return deny(503, 'Autenticação indisponível')
        request.state.principal = username
        response = await call_next(request)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Referrer-Policy'] = 'no-referrer'
        return response
