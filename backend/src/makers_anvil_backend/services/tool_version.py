"""Purpose: Read maker-tool version metadata without starting an external process.

Used by: ``ToolDetectionService`` after one allowlisted executable is detected.
Inputs: One privately resolved executable path and normalized operating-system id.
Outputs: Product/file version evidence or ``None`` when metadata is unavailable.
Side effects: Reads bounded operating-system metadata only; never writes or executes.
Safety: Paths remain private and no command, registry query, or tool launch is used.
Failure behavior: Missing, malformed, linked, or unsupported metadata stays unproven.
Related proof: ``tests/test_tool_version.py`` and tool-detection schema tests.
"""

from __future__ import annotations

import ctypes
import plistlib
import re
import sys
from pathlib import Path
from typing import TypedDict


VERSION_TEXT = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._+\-]{0,63}$")
WINDOWS_VERSION_SIGNATURE = 0xFEEF04BD
MAX_VERSION_METADATA_BYTES = 1_048_576


class ToolVersionEvidence(TypedDict):
    """Purpose: Name the closed metadata fields returned to tool detection.

    Inputs: Product version, file version, preferred value, and evidence method.
    Outputs: A typed in-memory mapping consumed by ``ToolDetectionService``.
    How it works: The declaration constrains key names for static analysis only.
    Side effects: None; declaring a ``TypedDict`` creates no runtime evidence.
    Failure behavior: Invalid runtime values are rejected before construction.
    Safety: The type intentionally has no filesystem-path or command field.
    Example: ``ToolVersionEvidence(value="4.5.0.0", fileVersion="4.5.0.0", productVersion="4.5.0.0", evidenceMethod="windows-version-resource")``.
    Related proof: ``tests/test_tool_version.py``.
    """

    value: str
    fileVersion: str
    productVersion: str
    evidenceMethod: str


class _VsFixedFileInfo(ctypes.Structure):
    """Purpose: Describe the fixed numeric block in a Windows version resource.

    Inputs: Bytes populated by the Windows ``VerQueryValueW`` API.
    Outputs: Named 32-bit fields containing file and product version components.
    How it works: ``ctypes`` maps the documented field order onto native memory.
    Side effects: None beyond reading memory owned by the local metadata buffer.
    Failure behavior: Signature and buffer-length checks reject incompatible data.
    Safety: The structure contains numeric metadata only, never code or a path.
    Example: ``_VsFixedFileInfo.from_buffer_copy(bytes(52))`` creates a zeroed test value.
    Related proof: Microsoft VERSIONINFO documentation and ``tests/test_tool_version.py``.
    """

    _fields_ = [
        ("signature", ctypes.c_uint32),
        ("structure_version", ctypes.c_uint32),
        ("file_version_ms", ctypes.c_uint32),
        ("file_version_ls", ctypes.c_uint32),
        ("product_version_ms", ctypes.c_uint32),
        ("product_version_ls", ctypes.c_uint32),
        ("file_flags_mask", ctypes.c_uint32),
        ("file_flags", ctypes.c_uint32),
        ("file_os", ctypes.c_uint32),
        ("file_type", ctypes.c_uint32),
        ("file_subtype", ctypes.c_uint32),
        ("file_date_ms", ctypes.c_uint32),
        ("file_date_ls", ctypes.c_uint32),
    ]


def read_tool_version(path: Path, platform_name: str) -> ToolVersionEvidence | None:
    """Purpose: Select the metadata-only reader for one normalized platform.

    Inputs: Private detected executable path and ``windows``, ``macos``, or other id.
    Outputs: Validated version evidence, otherwise ``None`` without guessing.
    How it works: Windows reads VERSIONINFO; macOS reads the containing app plist.
    Side effects: Reads one executable resource or one bundle plist; writes nothing.
    Failure behavior: Expected OS, parse, permission, and missing-file errors return ``None``.
    Safety: No subprocess, shell, registry, package manager, or path serialization exists.
    Example: ``read_tool_version(Path("Tool.exe"), "windows")`` may return numeric PE metadata.
    Related proof: ``tests/test_tool_version.py`` and ``tests/test_tool_detection.py``.
    """

    try:
        if platform_name == "windows" and sys.platform.startswith("win"):
            return _read_windows_version_resource(path)
        if platform_name == "macos":
            return _read_macos_bundle_info(path)
    except (OSError, ValueError, plistlib.InvalidFileException):
        return None
    return None


def _read_windows_version_resource(path: Path) -> ToolVersionEvidence | None:
    """Purpose: Read numeric file/product versions from a local Windows PE resource.

    Inputs: One privately detected ``.exe`` path that must be a regular non-link file.
    Outputs: Proven numeric version fields or ``None`` when VERSIONINFO is absent.
    How it works: Calls read-only ``version.dll`` APIs and validates the fixed signature.
    Side effects: The operating system reads local file metadata into process memory.
    Failure behavior: Missing resources, bad signatures, zero versions, and API failures return ``None``.
    Safety: The executable is never loaded as code, started, modified, or returned by path.
    Example: Blender's PE VERSIONINFO can produce ``4.5.0.0`` without running Blender.
    Related proof: ``tests/test_tool_version.py`` and Windows package smoke evidence.
    """

    if path.suffix.lower() != ".exe" or path.is_symlink() or not path.is_file():
        return None

    version_api = ctypes.WinDLL("version", use_last_error=True)
    get_size = version_api.GetFileVersionInfoSizeW
    get_size.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    get_size.restype = ctypes.c_uint32
    get_info = version_api.GetFileVersionInfoW
    get_info.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    get_info.restype = ctypes.c_int
    query_value = version_api.VerQueryValueW
    query_value.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint32)]
    query_value.restype = ctypes.c_int

    ignored_handle = ctypes.c_uint32(0)
    size = get_size(str(path), ctypes.byref(ignored_handle))
    if size < ctypes.sizeof(_VsFixedFileInfo) or size > MAX_VERSION_METADATA_BYTES:
        return None
    buffer = ctypes.create_string_buffer(size)
    if not get_info(str(path), 0, size, ctypes.cast(buffer, ctypes.c_void_p)):
        return None
    fixed_pointer = ctypes.c_void_p()
    fixed_length = ctypes.c_uint32(0)
    if not query_value(
        ctypes.cast(buffer, ctypes.c_void_p),
        "\\",
        ctypes.byref(fixed_pointer),
        ctypes.byref(fixed_length),
    ):
        return None
    if fixed_length.value < ctypes.sizeof(_VsFixedFileInfo) or not fixed_pointer.value:
        return None

    fixed = ctypes.cast(fixed_pointer, ctypes.POINTER(_VsFixedFileInfo)).contents
    if fixed.signature != WINDOWS_VERSION_SIGNATURE:
        return None
    file_version = _format_version_quad(fixed.file_version_ms, fixed.file_version_ls)
    product_version = _format_version_quad(fixed.product_version_ms, fixed.product_version_ls)
    if file_version == "0.0.0.0" and product_version == "0.0.0.0":
        return None
    preferred = product_version if product_version != "0.0.0.0" else file_version
    return ToolVersionEvidence(
        value=preferred,
        fileVersion=file_version,
        productVersion=product_version,
        evidenceMethod="windows-version-resource",
    )


def _read_macos_bundle_info(path: Path) -> ToolVersionEvidence | None:
    """Purpose: Read version strings from the containing macOS application bundle.

    Inputs: One privately detected executable nested beneath ``SomeTool.app``.
    Outputs: Validated bundle and short version evidence, otherwise ``None``.
    How it works: Finds the nearest app ancestor and parses ``Contents/Info.plist``.
    Side effects: Reads one bounded property-list file and performs no execution.
    Failure behavior: Links, malformed bundles, missing keys, or unsafe strings return ``None``.
    Safety: No LaunchServices call, command, process, or public path is created.
    Example: ``FreeCAD.app`` can prove its bundle version while FreeCAD stays closed.
    Related proof: ``tests/test_tool_version.py``.
    """

    if path.is_symlink() or not path.is_file():
        return None
    app_root = next((parent for parent in path.parents if parent.name.lower().endswith(".app")), None)
    if app_root is None or app_root.is_symlink():
        return None
    plist_path = app_root / "Contents" / "Info.plist"
    if plist_path.is_symlink() or not plist_path.is_file() or plist_path.stat().st_size > MAX_VERSION_METADATA_BYTES:
        return None
    with plist_path.open("rb") as stream:
        encoded = stream.read(MAX_VERSION_METADATA_BYTES + 1)
    if len(encoded) > MAX_VERSION_METADATA_BYTES:
        return None
    payload = plistlib.loads(encoded)
    if not isinstance(payload, dict):
        return None
    product_version = _normalize_version_text(payload.get("CFBundleShortVersionString"))
    file_version = _normalize_version_text(payload.get("CFBundleVersion"))
    preferred = product_version or file_version
    if preferred is None:
        return None
    return ToolVersionEvidence(
        value=preferred,
        fileVersion=file_version or preferred,
        productVersion=product_version or preferred,
        evidenceMethod="macos-bundle-info",
    )


def _format_version_quad(ms_value: int, ls_value: int) -> str:
    """Purpose: Convert two packed Windows DWORD values into four decimal components.

    Inputs: Most-significant and least-significant unsigned 32-bit values.
    Outputs: Stable ``major.minor.patch.build`` text with no locale dependency.
    How it works: Extracts each high and low 16-bit word using shifts and masks.
    Side effects: None; this is a deterministic numeric transformation.
    Failure behavior: Python integer masking safely bounds oversized test inputs.
    Safety: No path, process, file, or external API is touched.
    Example: ``_format_version_quad(0x00040005, 0x00000002)`` returns ``4.5.0.2``.
    Related proof: ``tests/test_tool_version.py``.
    """

    parts = (
        (ms_value >> 16) & 0xFFFF,
        ms_value & 0xFFFF,
        (ls_value >> 16) & 0xFFFF,
        ls_value & 0xFFFF,
    )
    return ".".join(str(part) for part in parts)


def _normalize_version_text(value: object) -> str | None:
    """Purpose: Accept a compact bundle version while rejecting arbitrary plist text.

    Inputs: One untrusted property-list value.
    Outputs: The bounded version string or ``None``.
    How it works: Requires a string matching the closed version-text expression.
    Side effects: None.
    Failure behavior: Empty, long, whitespace-bearing, or punctuation-rich values fail closed.
    Safety: Bounded text cannot carry a path, command line, or large private payload.
    Example: ``_normalize_version_text("1.2.3")`` returns ``1.2.3``.
    Related proof: ``tests/test_tool_version.py``.
    """

    return value if isinstance(value, str) and VERSION_TEXT.fullmatch(value) else None
