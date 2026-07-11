"""Purpose: Guard every bounded local mutation with process and browser evidence.

Used by: Authorized intake and persisted workbench preference services.
Inputs: A process-local token plus Origin, Host, and Fetch Metadata headers.
Outputs: Validation success or a stable path-free ``LocalRequestError``.
Side effects: Generates one memory-only token when production does not inject one.
Safety: Requires exact same-origin loopback HTTP and never persists the token.
Failure behavior: Missing, malformed, cross-site, or non-loopback evidence fails closed.
Related proof: ``tests/test_local_request_guard.py`` and API mutation tests.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass
from urllib.parse import urlsplit


class LocalRequestError(ValueError):
    """Purpose: Carry a stable HTTP rejection for a local mutation guard.

    Inputs: HTTP status, machine-readable code, and reviewed user-safe message.
    Outputs: Exception exposing ``status`` and ``code`` beside normal message text.
    How it works: Stores bounded response metadata before initializing ``ValueError``.
    Side effects: None until a caller raises and catches the instance.
    Failure behavior: Invalid constructor values remain visible programming defects.
    Safety: Messages are designed to exclude tokens, origins, and filesystem paths.
    Example: A cross-site request raises code ``cross_origin_rejected``.
    Related proof: ``tests/test_local_request_guard.py``.
    """

    def __init__(self, status: int, code: str, message: str) -> None:
        """Purpose: Initialize one typed local-request rejection.

        Inputs: HTTP status, stable snake-case code, and a path-free message.
        Outputs: Initialized exception instance; constructors return ``None``.
        How it works: Saves public fields and delegates message storage to ``ValueError``.
        Side effects: None.
        Failure behavior: Invalid caller constants are not silently normalized.
        Safety: No request evidence is copied into the exception message.
        Example: ``LocalRequestError(403, 'origin_rejected', 'Origin invalid.')``.
        Related proof: API error mapping tests.
        """

        super().__init__(message)
        self.status = status
        self.code = code


@dataclass(frozen=True)
class LocalRequestContext:
    """Purpose: Make browser security evidence explicit at each mutation boundary.

    Inputs: Process token, HTTP Origin/Host, and Sec-Fetch-Site relationship.
    Outputs: Immutable values consumed by ``LocalRequestGuard.validate``.
    How it works: Dataclass generation supplies typed construction and attributes.
    Side effects: None.
    Failure behavior: Empty or malformed fields are rejected by the guard.
    Safety: Callers cannot accidentally omit security evidence from a service call.
    Example: Same-origin loopback fetch supplies token, origin, host, and site.
    Related proof: Origin, token, host, and fetch-site rejection tests.
    """

    request_token: str
    origin: str
    host: str
    fetch_site: str


class LocalRequestGuard:
    """Purpose: Validate one process token and exact loopback same-origin evidence.

    Inputs: Optional deterministic token for tests and a ``LocalRequestContext``.
    Outputs: ``None`` on success or a typed rejection on any missing evidence.
    How it works: Constant-time compares token, parses Origin, then matches Host.
    Side effects: Production construction generates a random memory-only token.
    Failure behavior: Every failed condition raises ``LocalRequestError``.
    Safety: Rejects CORS-style, credential-bearing, non-HTTP, and remote origins.
    Example: ``http://127.0.0.1:8766`` must exactly match the Host header.
    Related proof: ``tests/test_local_request_guard.py``.
    """

    def __init__(self, request_token: str | None = None) -> None:
        """Purpose: Create or accept the token shared by guarded local services.

        Inputs: Optional nonempty token used by deterministic tests.
        Outputs: Initialized guard with a process-lifetime token.
        How it works: Uses ``token_urlsafe`` only when no token was supplied.
        Side effects: Generates random bytes in memory during production startup.
        Failure behavior: An explicitly empty token is rejected as configuration error.
        Safety: The token is not written to disk or included in ordinary app state.
        Example: Tests construct ``LocalRequestGuard('request-token')``.
        Related proof: Token lifecycle and API session tests.
        """

        if request_token == "":
            raise ValueError("local request token cannot be empty")
        self._request_token = request_token or secrets.token_urlsafe(32)

    @property
    def request_token(self) -> str:
        """Purpose: Supply the shared token to the same-origin session endpoint.

        Inputs: No caller values beyond this guard instance.
        Outputs: Current process-local request token.
        How it works: Returns the immutable private token value.
        Side effects: None.
        Failure behavior: Construction guarantees the value exists.
        Safety: Callers must expose it only through a no-CORS same-origin endpoint.
        Example: Intake session returns this value to its own workbench controller.
        Related proof: Session and cross-origin server tests.
        """

        return self._request_token

    def validate(self, context: LocalRequestContext) -> None:
        """Purpose: Require complete same-origin loopback evidence before mutation.

        Inputs: Token, Origin, Host, and Sec-Fetch-Site request values.
        Outputs: ``None`` only after every guard condition passes.
        How it works: Checks token/site, parses Origin, and matches loopback Host.
        Side effects: None.
        Failure behavior: Raises a stable 403 ``LocalRequestError`` on first failure.
        Safety: Cross-site forms and scripts cannot use the local mutation services.
        Example: Origin and Host ``127.0.0.1:8766`` with same-origin can pass.
        Related proof: ``tests/test_local_request_guard.py``.
        """

        if not context.request_token or not hmac.compare_digest(context.request_token, self._request_token):
            raise LocalRequestError(403, "request_token_rejected", "The local request token is missing or invalid.")
        if context.fetch_site != "same-origin":
            raise LocalRequestError(403, "cross_origin_rejected", "Local mutations require a same-origin browser request.")
        try:
            parsed_origin = urlsplit(context.origin)
        except ValueError as exc:
            raise LocalRequestError(403, "origin_rejected", "The local request origin is invalid.") from exc
        if parsed_origin.scheme != "http" or not parsed_origin.hostname or parsed_origin.username or parsed_origin.password:
            raise LocalRequestError(403, "origin_rejected", "The local request origin is invalid.")
        if parsed_origin.netloc.lower() != context.host.strip().lower():
            raise LocalRequestError(403, "origin_rejected", "The local request origin does not match the app.")
        if parsed_origin.hostname.lower() not in {"127.0.0.1", "localhost", "::1"}:
            raise LocalRequestError(403, "origin_rejected", "Local mutations require a loopback origin.")


__all__ = ["LocalRequestContext", "LocalRequestError", "LocalRequestGuard"]
