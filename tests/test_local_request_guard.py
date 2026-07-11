"""Purpose: Prove the shared mutation guard accepts only exact local app requests.

Used by: CI before intake or preference mutation code may ship.
Inputs: Deterministic token and focused request-context examples.
Outputs: Assertions for accepted loopback and rejected token/origin/site evidence.
Side effects: None; no server, filesystem, or application state is used.
Safety: Every mutation consumer receives the same fail-closed rules.
Failure behavior: Any weakened guard condition fails a named assertion.
Related proof: ``services/local_request_guard.py`` and API guard tests.
"""

import pytest

from makers_anvil_backend.services.local_request_guard import LocalRequestContext, LocalRequestError, LocalRequestGuard


TOKEN = "fixed-test-token"


def context(**changes: str) -> LocalRequestContext:
    """Purpose: Build known-good loopback evidence with focused replacements.

    Inputs: Optional dataclass field overrides for negative examples.
    Outputs: Immutable local request context.
    How it works: Merges overrides into one exact same-origin baseline.
    Side effects: None.
    Failure behavior: Unknown keys fail through dataclass construction.
    Safety: This helper grants no bypass; the real guard validates every field.
    Example: ``context(fetch_site='cross-site')`` models hostile browser metadata.
    Related proof: Tests below cover each evidence class.
    """

    values = {"request_token": TOKEN, "origin": "http://127.0.0.1:8766", "host": "127.0.0.1:8766", "fetch_site": "same-origin"}
    values.update(changes)
    return LocalRequestContext(**values)


def test_guard_accepts_exact_loopback_same_origin() -> None:
    """Purpose: Confirm complete legitimate local browser evidence passes.

    Inputs: Fixed token and matching loopback origin/host/site context.
    Outputs: No exception and exact request-token property assertion.
    How it works: Calls the same guard method used by production services.
    Side effects: None.
    Failure behavior: Any rejection fails the test directly.
    Safety: Success is limited to this complete exact evidence set.
    Example: Models the pywebview/browser workbench on port 8766.
    Related proof: Server same-origin fetch smoke.
    """

    guard = LocalRequestGuard(TOKEN)
    guard.validate(context())
    assert guard.request_token == TOKEN


@pytest.mark.parametrize(
    ("changes", "code"),
    [
        ({"request_token": "wrong"}, "request_token_rejected"),
        ({"fetch_site": "cross-site"}, "cross_origin_rejected"),
        ({"origin": "http://example.test:8766"}, "origin_rejected"),
        ({"host": "localhost:8766"}, "origin_rejected"),
    ],
)
def test_guard_rejects_incomplete_or_remote_evidence(changes: dict[str, str], code: str) -> None:
    """Purpose: Prove token, fetch-site, origin, and host checks fail closed.

    Inputs: One changed evidence field and its expected stable error code.
    Outputs: Typed 403 rejection with the named code.
    How it works: Parameterization exercises each independent guard boundary.
    Side effects: None.
    Failure behavior: Acceptance or wrong classification fails explicitly.
    Safety: Rejection messages do not echo token or origin values.
    Example: Remote example.test cannot mutate localhost state.
    Related proof: API error mapping and no-CORS server headers.
    """

    with pytest.raises(LocalRequestError) as caught:
        LocalRequestGuard(TOKEN).validate(context(**changes))
    assert caught.value.status == 403
    assert caught.value.code == code
