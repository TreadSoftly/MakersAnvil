"""Purpose: Translate loopback HTTP requests into read-only service calls.

Used by: ``server.RequestHandler`` for every ``/api/*`` request.
Inputs: An HTTP method and normalized URL path plus composed service state.
Outputs: An HTTP-like status code and a JSON-serializable response mapping.
Side effects: None; route handling reads state and never writes or launches.
Safety: Non-GET methods and unknown routes fail closed at this boundary.
Failure behavior: Unsupported requests return explicit 404 or 405 records.
Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
"""

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
    """Purpose: HTTP-ready API response.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``ApiResponse`` exposing the state and operations defined below.
    How it works: It executes the focused statements in source order.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Non-GET methods and unknown routes fail closed at this boundary.
    Example: Construct with ``instance = ApiResponse(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
    """

    status: int
    body: JsonDict
    headers: dict[str, str] = field(default_factory=lambda: {"Content-Type": "application/json; charset=utf-8"})


class MakersAnvilApi:
    """Purpose: Route read-only API requests to deterministic service responses.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``MakersAnvilApi`` exposing the state and operations defined below.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Non-GET methods and unknown routes fail closed at this boundary.
    Example: Construct with ``instance = MakersAnvilApi(...)`` using values described by ``__init__``.
    Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
    """

    def __init__(self, state_service: AppStateService | None = None) -> None:
        """Purpose: Register every allowed read route against one composable state service.

        Inputs: Caller-supplied ``state_service`` values from the signature.
        Outputs: The initialized instance state; Python constructors return ``None``.
        How it works: It executes the focused statements in source order.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Non-GET methods and unknown routes fail closed at this boundary.
        Example: Create the owning class with values matching this constructor signature.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        self._state_service = state_service or AppStateService()
        self._routes: dict[str, RouteHandler] = {
            "/api/health": self._state_service.health,
            "/api/state": self._state_service.state,
            "/api/claim-states": self._claim_states,
            "/api/workspace/status": self._state_service.workspace_status,
            "/api/passes/ledger": self._state_service.pass_ledger,
            "/api/workspace/config": self._state_service.workspace_config,
            "/api/workspace/layout": self._state_service.workspace_layout,
            "/api/intake/policy": self._state_service.intake_policy,
            "/api/intake/catalog": self._state_service.intake_catalog,
            "/api/routes/preview": self._state_service.route_preview,
            "/api/outputs/preview": self._state_service.output_proof,
            "/api/tools/detection": self._state_service.tool_detection,
            "/api/tools/dry-run": self._state_service.tool_dry_run,
            "/api/execution/gates": self._state_service.execution_gates,
            "/api/execution/requests/preview": self._state_service.execution_request_preview,
            "/api/jobs/policy": self._state_service.job_workspace_policy,
            "/api/jobs/catalog": self._state_service.job_workspace_catalog,
        }

    def handle(self, method: str, raw_path: str) -> ApiResponse:
        """Purpose: Return a deterministic response while rejecting every non-GET API request.

        Inputs: Caller-supplied ``method``, ``raw_path`` values from the signature.
        Outputs: Returns ``ApiResponse``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Non-GET methods and unknown routes fail closed at this boundary.
        Example: Call ``result = instance.handle(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

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
        """Purpose: Expose the closed claim-state vocabulary used by every public contract.

        Inputs: No caller-supplied values beyond an implicit instance/class when present.
        Outputs: Returns ``JsonDict``, or raises before returning when validation fails.
        How it works: It returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: Non-GET methods and unknown routes fail closed at this boundary.
        Example: Call ``result = instance._claim_states(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        return {
            "schemaVersion": "makers-anvil.api.claim-states.v1",
            "claimState": "proven",
            "states": list(ALLOWED_CLAIM_STATES),
        }
