"""Unit tests for docs/scripts/migrate_from_v2.py's environment ghost-file scan.

This script lives outside the installable package (it's a standalone
migration helper), so it's imported here by path rather than as
`neo_api_client.*`.
"""

import importlib.util
import sys
import types
from pathlib import Path

_SCRIPT_PATH = Path(__file__).resolve().parents[2] / "docs" / "scripts" / "migrate_from_v2.py"
_spec = importlib.util.spec_from_file_location("migrate_from_v2", _SCRIPT_PATH)
migrate_from_v2 = importlib.util.module_from_spec(_spec)
sys.modules["migrate_from_v2"] = migrate_from_v2  # dataclass() needs this registered first
_spec.loader.exec_module(migrate_from_v2)


def _install_fake_neo_api_client(monkeypatch, pkg_dir: Path):
    """Make `import neo_api_client` resolve to a fake module whose
    `__file__` points at `pkg_dir/__init__.py`, without touching the real
    installed package."""
    fake_init = pkg_dir / "__init__.py"
    fake_init.parent.mkdir(parents=True, exist_ok=True)
    fake_init.touch()
    fake_module = types.ModuleType("neo_api_client")
    fake_module.__file__ = str(fake_init)
    monkeypatch.setitem(sys.modules, "neo_api_client", fake_module)


def test_no_findings_when_no_ghost_files_present(monkeypatch, tmp_path):
    _install_fake_neo_api_client(monkeypatch, tmp_path / "neo_api_client")

    assert migrate_from_v2.scan_installed_environment_for_ghost_files() == []


def test_finds_neo_websocket_ghost_file(monkeypatch, tmp_path):
    pkg_dir = tmp_path / "neo_api_client"
    _install_fake_neo_api_client(monkeypatch, pkg_dir)
    (pkg_dir / "NeoWebSocket.py").write_text("# legacy leftover\n")

    findings = migrate_from_v2.scan_installed_environment_for_ghost_files()

    assert len(findings) == 1
    assert findings[0].file == pkg_dir / "NeoWebSocket.py"
    assert findings[0].severity == "warning"
    assert "neo-api-client" in findings[0].message


def test_finds_both_ghost_files_as_separate_findings(monkeypatch, tmp_path):
    pkg_dir = tmp_path / "neo_api_client"
    _install_fake_neo_api_client(monkeypatch, pkg_dir)
    (pkg_dir / "NeoWebSocket.py").write_text("# legacy leftover\n")
    (pkg_dir / "HSWebSocketLib.py").write_text("# legacy leftover\n")

    findings = migrate_from_v2.scan_installed_environment_for_ghost_files()

    assert {f.file.name for f in findings} == {"NeoWebSocket.py", "HSWebSocketLib.py"}


def test_finds_only_the_ghost_file_that_actually_exists(monkeypatch, tmp_path):
    """Regression: a prior version of this check always pointed its finding
    at NeoWebSocket.py even when only HSWebSocketLib.py was present,
    reporting a location that doesn't exist on disk."""
    pkg_dir = tmp_path / "neo_api_client"
    _install_fake_neo_api_client(monkeypatch, pkg_dir)
    (pkg_dir / "HSWebSocketLib.py").write_text("# legacy leftover\n")

    findings = migrate_from_v2.scan_installed_environment_for_ghost_files()

    assert len(findings) == 1
    assert findings[0].file == pkg_dir / "HSWebSocketLib.py"
    assert findings[0].file.exists()


def test_returns_empty_list_when_neo_api_client_not_importable(monkeypatch):
    monkeypatch.setitem(sys.modules, "neo_api_client", None)  # import raises ImportError

    assert migrate_from_v2.scan_installed_environment_for_ghost_files() == []


def test_main_includes_environment_findings_alongside_source_findings(
    monkeypatch, tmp_path, capsys
):
    pkg_dir = tmp_path / "neo_api_client"
    _install_fake_neo_api_client(monkeypatch, pkg_dir)
    (pkg_dir / "NeoWebSocket.py").write_text("# legacy leftover\n")

    clean_file = tmp_path / "clean.py"
    clean_file.write_text("x = 1\n")

    exit_code = migrate_from_v2.main([str(clean_file)])

    captured = capsys.readouterr()
    assert "NeoWebSocket.py" in captured.out
    assert "[WARNING]" in captured.out
    assert exit_code == 0  # a "warning"-only ghost-file finding must not fail the scan
