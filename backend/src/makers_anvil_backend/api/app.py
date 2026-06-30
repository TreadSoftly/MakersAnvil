"""Purpose: Translate loopback HTTP requests into safe service calls.

Used by: ``server.RequestHandler`` for every ``/api/*`` request.
Inputs: HTTP method/path, bounded body/stream, security headers, and service state.
Outputs: An HTTP-like status code and a JSON-serializable response mapping.
Side effects: Two intake POST routes may write app-owned authorized content.
Safety: Every other mutation, unknown route, execution, and launch fails closed.
Failure behavior: Unsupported requests return explicit 404 or 405 records.
Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, BinaryIO, Callable, Mapping
from urllib.parse import urlparse

from makers_anvil_backend.domain.claim_state import ALLOWED_CLAIM_STATES
from makers_anvil_backend.services.app_state import AppStateService
from makers_anvil_backend.services.authorized_intake import IntakeRequestContext, IntakeTransferError
from makers_anvil_backend.services.intake_catalog import IntakeCatalogError
from makers_anvil_backend.services.local_request_guard import LocalRequestError
from makers_anvil_backend.services.workbench_experience import WorkbenchExperienceError


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
    """Purpose: Route read APIs and exactly two guarded intake mutations.

    Inputs: Constructor values documented by ``__init__``; class methods receive the resulting instance.
    Outputs: An instance of ``MakersAnvilApi`` exposing the state and operations defined below.
    How it works: It checks conditions, then returns the resulting contract value.
    Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
    Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
    Safety: Only explicit one-file intake may mutate; all other methods fail closed.
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
            "/api/intake/session": self._state_service.intake_session,
            "/api/routes/preview": self._state_service.route_preview,
            "/api/outputs/preview": self._state_service.output_proof,
            "/api/tools/detection": self._state_service.tool_detection,
            "/api/tools/dry-run": self._state_service.tool_dry_run,
            "/api/execution/gates": self._state_service.execution_gates,
            "/api/execution/requests/preview": self._state_service.execution_request_preview,
            "/api/jobs/policy": self._state_service.job_workspace_policy,
            "/api/jobs/catalog": self._state_service.job_workspace_catalog,
            "/api/workbench/experience": self._state_service.workbench_experience,
            "/api/activity/recent": self._state_service.activity_history,
            "/api/capabilities/matrix": self._state_service.capability_matrix,
        }

    def handle(
        self,
        method: str,
        raw_path: str,
        *,
        headers: Mapping[str, str] | None = None,
        body: bytes | None = None,
        body_stream: BinaryIO | None = None,
        content_length: int | None = None,
    ) -> ApiResponse:
        """Purpose: Dispatch reads or the two guarded one-file intake POST routes.

        Inputs: Method/path plus optional headers, bounded JSON body, stream, and length.
        Outputs: Returns ``ApiResponse``, or raises before returning when validation fails.
        How it works: It checks conditions, then returns the resulting contract value.
        Side effects: No side effect is implied beyond calls visible in the body; external effects must remain explicit and tested.
        Failure behavior: Unexpected exceptions propagate to the caller so missing evidence is never converted into a success claim.
        Safety: All methods except GET and two exact POST shapes fail closed.
        Example: Call ``result = instance.handle(...)`` with values satisfying the documented inputs.
        Related proof: ``tests/test_api.py`` and ``schemas/app-state.schema.json``.
        """

        path = urlparse(raw_path).path
        normalized_method = method.upper()
        if normalized_method == "POST":
            return self._handle_post(path, headers or {}, body, body_stream, content_length)
        if normalized_method != "GET":
            return ApiResponse(
                405,
                {
                    "schemaVersion": "makers-anvil.api.error.v1",
                    "claimState": "blocked",
                    "error": "method_not_allowed",
                    "message": "This state-changing request is blocked.",
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

    def _handle_post(
        self,
        path: str,
        headers: Mapping[str, str],
        body: bytes | None,
        body_stream: BinaryIO | None,
        content_length: int | None,
    ) -> ApiResponse:
        """Purpose: Handle guarded intake or complete workbench preference JSON.

        Inputs: Exact API path, normalized HTTP headers, body/stream, and length.
        Outputs: 201 response or stable path-free error response.
        How it works: Matches two routes, validates media type, then delegates service rules.
        Side effects: Successful calls write app-owned intake, settings, or activity records.
        Failure behavior: JSON, guard, policy, replay, size, and I/O failures are explicit.
        Safety: Unknown POSTs never reach a service and receive method-not-allowed.
        Example: Authorization JSON precedes ``/<authorization-id>/content`` bytes.
        Related proof: API/server tests and ``AuthorizedIntakeService`` tests.
        """

        normalized_headers = {key.lower(): value for key, value in headers.items()}
        context = IntakeRequestContext(
            request_token=normalized_headers.get("x-makers-anvil-request-token", ""),
            origin=normalized_headers.get("origin", ""),
            host=normalized_headers.get("host", ""),
            fetch_site=normalized_headers.get("sec-fetch-site", ""),
        )
        try:
            if path == "/api/intake/authorizations":
                media_type = normalized_headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if media_type != "application/json" or body is None:
                    return self._api_error(415, "content_type_not_allowed", "Authorization requires an application/json body.")
                try:
                    metadata = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return self._api_error(400, "json_invalid", "Authorization metadata must be valid UTF-8 JSON.")
                if not isinstance(metadata, dict):
                    return self._api_error(400, "metadata_invalid", "Authorization metadata must be a JSON object.")
                result = self._state_service.create_intake_authorization(metadata, context)
                return ApiResponse(201, result)

            if path == "/api/workbench/experience":
                media_type = normalized_headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if media_type != "application/json" or body is None:
                    return self._api_error(415, "content_type_not_allowed", "Workbench preferences require an application/json body.")
                try:
                    preferences = json.loads(body.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    return self._api_error(400, "json_invalid", "Workbench preferences must be valid UTF-8 JSON.")
                if not isinstance(preferences, dict):
                    return self._api_error(400, "preferences_invalid", "Workbench preferences must be a JSON object.")
                result = self._state_service.update_workbench_experience(preferences, context)
                return ApiResponse(200, result)

            prefix = "/api/intake/authorizations/"
            suffix = "/content"
            if path.startswith(prefix) and path.endswith(suffix):
                authorization_id = path[len(prefix) : -len(suffix)]
                media_type = normalized_headers.get("content-type", "").split(";", 1)[0].strip().lower()
                if media_type != "application/octet-stream" or body_stream is None:
                    return self._api_error(415, "content_type_not_allowed", "Authorized content requires application/octet-stream.")
                if content_length is None or content_length < 0:
                    return self._api_error(411, "content_length_required", "Authorized content requires an exact Content-Length.")
                result = self._state_service.ingest_authorized_file(
                    authorization_id,
                    body_stream,
                    content_length,
                    context,
                )
                return ApiResponse(201, result)
        except IntakeTransferError as exc:
            return self._api_error(exc.status, exc.code, str(exc))
        except LocalRequestError as exc:
            return self._api_error(exc.status, exc.code, str(exc))
        except WorkbenchExperienceError as exc:
            return self._api_error(422, "preferences_invalid", str(exc))
        except IntakeCatalogError:
            return self._api_error(422, "intake_record_invalid", "The authorized intake record was rejected.")
        except OSError:
            return self._api_error(500, "intake_storage_failed", "App-owned intake storage could not complete the request.")

        return ApiResponse(
            405,
            {
                "schemaVersion": "makers-anvil.api.error.v1",
                "claimState": "blocked",
                "error": "method_not_allowed",
                "message": "Only documented guarded intake and workbench-preference POST routes are enabled.",
                "allowedMethods": ["GET"],
            },
        )

    @staticmethod
    def _api_error(status: int, code: str, message: str) -> ApiResponse:
        """Purpose: Build one stable JSON error without leaking private request data.

        Inputs: HTTP status, machine-readable code, and reviewed user-facing message.
        Outputs: ``ApiResponse`` with blocked or failed claim state.
        How it works: Treats 4xx as blocked and 5xx as failed.
        Side effects: None.
        Failure behavior: Invalid caller values remain visible programming defects.
        Safety: Response shape has no path, token, origin, stack, or byte content.
        Example: An oversize file returns 413 and ``file_too_large``.
        Related proof: API error mapping tests.
        """

        return ApiResponse(
            status,
            {
                "schemaVersion": "makers-anvil.api.error.v1",
                "claimState": "blocked" if status < 500 else "failed",
                "error": code,
                "message": message,
            },
        )

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
