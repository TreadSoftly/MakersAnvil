"""Purpose: Prove metadata-only tool version readers without launching software.

Used by: Developers and CI when Windows/macOS version evidence changes.
Inputs: Isolated executable and application-bundle fixtures.
Outputs: Assertions for numeric packing, bundle parsing, and fail-closed cases.
Side effects: Writes only pytest temporary fixtures; starts no process.
Safety: Tests never inspect real installed tools or expose a private path.
Failure behavior: Missing or malformed metadata must return ``None``.
Related proof: ``services/tool_version.py`` and tool-detection schema.
"""

import plistlib
from pathlib import Path

from makers_anvil_backend.services.tool_version import _format_version_quad, read_tool_version


def test_formats_packed_windows_version_components() -> None:
    """Purpose: Prove DWORD version words become stable four-part text.

    Inputs: Two deterministic packed integer values.
    Outputs: No return; one assertion proves major/minor/patch/build order.
    How it works: Calls the pure formatter with known high and low words.
    Side effects: None.
    Failure behavior: A failed assertion identifies packing or ordering regression.
    Safety: No operating-system metadata or process API is touched.
    Example: Packed ``4,5,0,2`` must become ``4.5.0.2``.
    Related proof: ``services/tool_version.py``.
    """

    assert _format_version_quad(0x00040005, 0x00000002) == "4.5.0.2"


def test_reads_macos_bundle_versions_without_executing(tmp_path: Path) -> None:
    """Purpose: Prove a bounded app plist can provide product and file versions.

    Inputs: Isolated ``Maker.app`` executable and ``Info.plist`` fixture.
    Outputs: No return; assertions prove the closed metadata record.
    How it works: Writes a tiny plist, then invokes the macOS metadata reader path.
    Side effects: Creates files only under pytest's temporary directory.
    Failure behavior: Parse, ancestry, key, or normalization regressions fail assertions.
    Safety: The fake executable bytes are never imported, loaded, or started.
    Example: Short version ``2.4.1`` and bundle ``2410`` remain distinct evidence.
    Related proof: ``services/tool_version.py`` and ``tests/test_tool_detection.py``.
    """

    app_root = tmp_path / "Maker.app"
    executable = app_root / "Contents" / "MacOS" / "maker"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"not executable")
    info_path = app_root / "Contents" / "Info.plist"
    with info_path.open("wb") as stream:
        plistlib.dump({"CFBundleShortVersionString": "2.4.1", "CFBundleVersion": "2410"}, stream)

    assert read_tool_version(executable, "macos") == {
        "value": "2.4.1",
        "fileVersion": "2410",
        "productVersion": "2.4.1",
        "evidenceMethod": "macos-bundle-info",
    }
    assert executable.read_bytes() == b"not executable"


def test_rejects_unbounded_macos_version_text(tmp_path: Path) -> None:
    """Purpose: Ensure plist fields cannot become arbitrary public display text.

    Inputs: Isolated app bundle containing whitespace-rich non-version values.
    Outputs: No return; ``None`` proves the evidence remains unproven.
    How it works: Creates valid plist syntax with values outside the version allowlist.
    Side effects: Creates files only under pytest's temporary directory.
    Failure behavior: Any evidence result indicates unsafe text normalization widened.
    Safety: Rejecting free text prevents path, command, and private payload display.
    Example: ``not a version`` is rejected because spaces are outside the grammar.
    Related proof: ``services/tool_version.py``.
    """

    app_root = tmp_path / "Maker.app"
    executable = app_root / "Contents" / "MacOS" / "maker"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"not executable")
    with (app_root / "Contents" / "Info.plist").open("wb") as stream:
        plistlib.dump({"CFBundleShortVersionString": "not a version"}, stream)

    assert read_tool_version(executable, "macos") is None


def test_caps_macos_plist_read_before_parsing(tmp_path: Path) -> None:
    """Purpose: Prove an oversized bundle plist cannot cause an unbounded metadata read.

    Inputs: Isolated app bundle with an ``Info.plist`` larger than one MiB.
    Outputs: No return; ``None`` proves the size gate runs before plist parsing.
    How it works: Writes a fixed oversized byte fixture and invokes the macOS reader.
    Side effects: Creates temporary bytes only under pytest's directory.
    Failure behavior: Evidence or a parse exception indicates the bounded-read gate regressed.
    Safety: The reader consumes at most its declared ceiling plus one sentinel byte.
    Example: A 1,048,577-byte plist remains not proven.
    Related proof: ``services/tool_version.py``.
    """

    app_root = tmp_path / "Maker.app"
    executable = app_root / "Contents" / "MacOS" / "maker"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"not executable")
    (app_root / "Contents" / "Info.plist").write_bytes(b"x" * 1_048_577)

    assert read_tool_version(executable, "macos") is None


def test_unsupported_platform_does_not_guess_from_filename(tmp_path: Path) -> None:
    """Purpose: Keep version-looking filenames from becoming invented evidence.

    Inputs: A regular file whose name contains a plausible version string.
    Outputs: No return; ``None`` proves unsupported platforms do not infer versions.
    How it works: Calls the dispatcher with the closed but unsupported ``linux`` path.
    Side effects: Creates one temporary file.
    Failure behavior: Any evidence means filename inference was incorrectly enabled.
    Safety: The application never claims a version from path text alone.
    Example: ``tool-9.9`` remains not proven.
    Related proof: ``services/tool_version.py``.
    """

    executable = tmp_path / "tool-9.9"
    executable.write_bytes(b"not executable")

    assert read_tool_version(executable, "linux") is None
