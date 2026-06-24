"""Purpose: Provide ``python -m makers_anvil_backend`` as a local entrypoint.

Used by: Developers launching the source checkout without a wrapper script.
Inputs: Process environment and command-line execution context.
Outputs: A loopback HTTP server delegated to ``server.main``.
Side effects: Starts a long-running local process only when executed directly.
Safety: Importing this module does not itself mutate product or user files.
Failure behavior: Server startup failures propagate to a nonzero process exit.
Related proof: ``tests/test_api.py`` and the runtime smoke test.
"""

from .server import main

raise SystemExit(main())
