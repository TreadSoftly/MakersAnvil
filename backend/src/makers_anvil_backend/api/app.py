"""Small read-only API facade for the current Makers Anvil build."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import urlparse

from makers_anvil_backend.domain.claim_state import ALLOWED_CLAIM_STATES
from makers_anvil_backend.services.app_state import AppStateService


JsonDict = dict[str, Any]
RouteHandler = Callable[[], JsonDict]


@dataclass(frozen=True)
class ApiResponse:
    """HTTP-ready API response."""

    status: int
    body: JsonDict
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json; charset=utf-8"})


class MakersAnvilApi:
    """Route read-only API requests to deterministic service responses."""

    def __init__(self, state_service: AppStateService | None = None) -> None:
        self._state_service = state_service or AppStateService()
        self._routes: dict[str, RouteHandler] = {
            "/api/health": self._state_service.health,
            "/api/state": self._state_service.state,
            "/api/claim-states": self._claim_states,
        }

    def handle(self, method: str, raw_path: str) -> ApiResponse:
        path = urlparse(raw_path).path
        normalized_method = method.upper()
        if normalized_method != "GET":
            return ApiResponse(
                405,
                {
                    "schemaVersion": "makers-anvil.api.error.v1",
                    "claimState": "blocked",
                    "error": "method_not_allowed",
                    "message": "State-changing requests are blocked in this build.",
                    "allowedMethods": ["GET"],
                },
            )

        handler = self._routes.get(path)
        if handler is None:
            return ApiResponse(
                404,
                {
                    "schemaVersion": "makers-anvil.api.error.v1",
                    "claimState": "not proven",
                    "error": "not_found",
                    "message": "No read-only API route exists for this path.",
                    "path": path,
                },
            )
        return ApiResponse(200, handler())

    def _claim_states(self) -> JsonDict:
        return {
            "schemaVersion": "makers-anvil.api.claim-states.v1",
            "claimState": "proven",
            "states": list(ALLOWED_CLAIM_STATES),
        }
