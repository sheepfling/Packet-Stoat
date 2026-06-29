from __future__ import annotations

import secrets
import time
from dataclasses import dataclass, field
from typing import Mapping


class AuthError(RuntimeError):
    def __init__(self, status_code: int, reason: str) -> None:
        super().__init__(reason)
        self.status_code = status_code
        self.reason = reason


@dataclass(frozen=True)
class TokenRecord:
    access_token: str
    subject: str
    scopes: frozenset[str]
    expires_at_unix_s: float
    token_type: str = "Bearer"

    def expires_in(self, now: float | None = None) -> int:
        current = time.time() if now is None else now
        return max(0, int(self.expires_at_unix_s - current))


@dataclass(frozen=True)
class MockLatticeAuthConfig:
    clients: Mapping[str, str] = field(default_factory=lambda: {"packet-stoat-client": "packet-stoat-secret"})
    environment_token: str = "mock-environment-token"
    sandbox_token: str = "mock-sandbox-token"
    token_ttl_seconds: int = 60
    require_sandbox_token: bool = True
    default_scopes: frozenset[str] = frozenset({"entities", "objects", "tasks", "streams"})


class MockLatticeAuthService:
    def __init__(self, config: MockLatticeAuthConfig | None = None) -> None:
        self.config = config or MockLatticeAuthConfig()
        self._tokens: dict[str, TokenRecord] = {}

    def issue_client_credentials_token(
        self,
        client_id: str,
        client_secret: str,
        *,
        scope: str | None = None,
        now: float | None = None,
    ) -> TokenRecord:
        expected = self.config.clients.get(client_id)
        if expected is None or expected != client_secret:
            raise AuthError(401, "invalid client credentials")
        scopes = frozenset(scope.split()) if scope else self.config.default_scopes
        current = time.time() if now is None else now
        token = f"mock-access-{secrets.token_urlsafe(24)}"
        record = TokenRecord(
            access_token=token,
            subject=client_id,
            scopes=scopes,
            expires_at_unix_s=current + self.config.token_ttl_seconds,
        )
        self._tokens[token] = record
        return record

    def oauth_token_response(
        self,
        *,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        scope: str | None = None,
    ) -> dict[str, object]:
        if grant_type != "client_credentials":
            raise AuthError(400, "unsupported grant_type")
        record = self.issue_client_credentials_token(client_id, client_secret, scope=scope)
        return {
            "access_token": record.access_token,
            "token_type": record.token_type,
            "expires_in": record.expires_in(),
            "scope": " ".join(sorted(record.scopes)),
        }

    def validate_headers(
        self,
        headers: Mapping[str, str],
        *,
        required_scope: str | None = None,
        now: float | None = None,
    ) -> TokenRecord:
        self.validate_sandbox_headers(headers)

        auth_header = headers.get("Authorization") or headers.get("authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            raise AuthError(401, "missing bearer token")
        token = auth_header.removeprefix("Bearer ").strip()
        if token == self.config.environment_token:
            record = TokenRecord(
                access_token=token,
                subject="environment-token",
                scopes=self.config.default_scopes,
                expires_at_unix_s=float("inf"),
            )
        else:
            record = self._tokens.get(token)
            if record is None:
                raise AuthError(401, "unknown bearer token")
            current = time.time() if now is None else now
            if record.expires_at_unix_s <= current:
                raise AuthError(401, "expired bearer token")

        if required_scope is not None and required_scope not in record.scopes:
            raise AuthError(403, f"missing required scope: {required_scope}")
        return record

    def validate_sandbox_headers(self, headers: Mapping[str, str]) -> None:
        if not self.config.require_sandbox_token:
            return
        sandbox_header = headers.get("Anduril-Sandbox-Authorization") or headers.get("anduril-sandbox-authorization")
        if sandbox_header != f"Bearer {self.config.sandbox_token}":
            raise AuthError(403, "missing or invalid sandbox authorization")

    def refresh_recommended(self, token: str, *, margin_seconds: int = 10, now: float | None = None) -> bool:
        record = self._tokens.get(token)
        if record is None:
            return False
        current = time.time() if now is None else now
        return record.expires_at_unix_s - current <= margin_seconds


__all__ = [
    "AuthError",
    "MockLatticeAuthConfig",
    "MockLatticeAuthService",
    "TokenRecord",
]
