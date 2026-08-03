#!/usr/bin/env python3
"""Migration helper: scan a project using neo-api-client (kotak-neo-api-v2)
and report the changes needed to move to kotakneoapi (kotak-neo-python).

Usage:
    python docs/scripts/migrate_from_v2.py /path/to/user/project
    python docs/scripts/migrate_from_v2.py file1.py file2.py

This tool never edits files. It only reports what needs manual attention,
because several v2 features (bracket/cover orders, per-order risk params,
callback-based WebSockets) have no direct equivalent in the new SDK and
require a human decision, not a mechanical rename.
"""

from __future__ import annotations

import argparse
import ast
import sys
from dataclasses import dataclass
from pathlib import Path

CLIENT_CONSTRUCTOR = "NeoAPI"

# Methods removed with no replacement. Calling these on the new SDK raises
# NotImplementedError (websocket) or AttributeError (bracket/cover orders).
REMOVED_METHODS: dict[str, str] = {
    "cancel_cover_order": (
        "Removed in kotakneoapi. Cover orders have no equivalent method — "
        "use cancel_order(order_id) if the position can be closed as a "
        "regular order, otherwise this needs a product-level decision."
    ),
    "cancel_bracket_order": (
        "Removed in kotakneoapi. Bracket orders have no equivalent method — "
        "use cancel_order(order_id) if applicable, otherwise this needs a "
        "product-level decision."
    ),
    "subscribe": (
        "Removed in kotakneoapi (raises NotImplementedError). The "
        "callback-based WebSocket was replaced by an async client: "
        "use `async with client.create_websocket() as ws:` and "
        "`await ws.subscribe_scrips(...)`. This is a sync-to-async rewrite, "
        "not a renamed call — see neo_api_client.websocket.feed.SFeedWebSocket."
    ),
    "un_subscribe": (
        "Removed in kotakneoapi (raises NotImplementedError). Use the async "
        "SFeedWebSocket's `unsubscribe_scrips(...)` on the object returned by "
        "`client.create_websocket()` instead."
    ),
    "subscribe_to_orderfeed": (
        "Removed in kotakneoapi (raises NotImplementedError). Use "
        "`async with client.create_order_feed() as feed:` instead."
    ),
}

# Keyword arguments accepted in v2 that are silently gone in kotakneoapi.
# Passing them as keywords now raises TypeError; passing them positionally
# in the old order maps to the wrong new parameter, which is worse.
DROPPED_KWARGS: dict[str, set[str]] = {
    "place_order": {
        "market_protection",
        "pf",
        "tag",
        "scrip_token",
        "square_off_type",
        "square_off_value",
        "stop_loss_type",
        "stop_loss_value",
        "last_traded_price",
        "trailing_stop_loss",
        "trailing_sl_value",
    },
    "modify_order": {
        "instrument_token",
        "exchange_segment",
        "product",
        "trading_symbol",
        "transaction_type",
        "dd",
        "market_protection",
        "filled_quantity",
    },
    "cancel_order": set(),  # amo/isVerify both kept; no drops.
    "trade_report": {"order_id"},  # trade_report() now takes no filter.
    "limits": {"segment", "exchange", "product"},  # limits() now takes none.
}

# Positional-argument-order changes. Any positional call to these is unsafe
# to auto-fix because argument N in v2 may not be argument N in the new SDK.
POSITIONAL_ORDER_CHANGED: dict[str, str] = {
    "NeoAPI": (
        "Constructor positional order changed: v2 was "
        "(environment, access_token, neo_fin_key, consumer_key); "
        "kotakneoapi is (consumer_key, environment, access_token, neo_fin_key). "
        "Also the environment default flipped from 'uat' to 'prod'. "
        "Call with keyword arguments to avoid silently swapping values."
    ),
}

PACKAGE_NAME_NOTE = (
    "PyPI package name changed: `pip install neo-api-client` -> "
    "`pip install kotakneoapi`. The import path (`neo_api_client`) is "
    "unchanged, so `import neo_api_client` / `from neo_api_client import "
    "NeoAPI` lines do not need to change."
)


@dataclass
class Finding:
    file: Path
    line: int
    severity: str  # "error" | "warning" | "info"
    message: str


def _call_name(node: ast.Call) -> str | None:
    func = node.func
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return None


def _kwarg_names(node: ast.Call) -> set[str]:
    return {kw.arg for kw in node.keywords if kw.arg is not None}


class MigrationVisitor(ast.NodeVisitor):
    # Method names are matched regardless of the receiver, since resolving
    # "is this variable actually a NeoAPI instance" reliably would need type
    # inference this tool doesn't do. This can over-report on unrelated
    # objects that happen to share a method name (e.g. some other class's
    # own `subscribe()`) — read findings with that in mind.

    def __init__(self, file: Path) -> None:
        self.file = file
        self.findings: list[Finding] = []

    def visit_Call(self, node: ast.Call) -> None:
        name = _call_name(node)

        if name == CLIENT_CONSTRUCTOR and node.args:
            note = POSITIONAL_ORDER_CHANGED[CLIENT_CONSTRUCTOR]
            self.findings.append(Finding(self.file, node.lineno, "error", f"NeoAPI(...): {note}"))

        if name in REMOVED_METHODS and isinstance(node.func, ast.Attribute):
            self.findings.append(
                Finding(
                    self.file,
                    node.lineno,
                    "error",
                    f"{name}(...): {REMOVED_METHODS[name]}",
                )
            )

        if name in DROPPED_KWARGS and isinstance(node.func, ast.Attribute):
            used = _kwarg_names(node) & DROPPED_KWARGS[name]
            if used:
                dropped = ", ".join(sorted(used))
                self.findings.append(
                    Finding(
                        self.file,
                        node.lineno,
                        "warning",
                        f"{name}(...): parameter(s) [{dropped}] no longer exist "
                        f"in kotakneoapi and will raise TypeError. Remove them "
                        f"or confirm the new SDK's reduced behavior is acceptable.",
                    )
                )
            if name in {"place_order", "modify_order"} and node.args:
                self.findings.append(
                    Finding(
                        self.file,
                        node.lineno,
                        "warning",
                        f"{name}(...): called with positional arguments. Some "
                        f"parameters were removed in kotakneoapi, so positions "
                        f"after the changed point may map to the wrong "
                        f"parameter. Switch to keyword arguments before relying "
                        f"on this call.",
                    )
                )

        self.generic_visit(node)


def scan_file(path: Path) -> list[Finding]:
    try:
        source = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [Finding(path, 0, "error", f"Could not read file: {exc}")]

    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as exc:
        return [Finding(path, exc.lineno or 0, "error", f"Syntax error: {exc.msg}")]

    visitor = MigrationVisitor(path)
    visitor.visit(tree)

    findings = visitor.findings
    if "neo-api-client" in source or "neo_api_client" in source:
        findings.append(Finding(path, 1, "info", PACKAGE_NAME_NOTE))
    return findings


def iter_python_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for p in paths:
        if p.is_dir():
            files.extend(sorted(p.rglob("*.py")))
        elif p.suffix == ".py":
            files.append(p)
    return files


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to scan")
    args = parser.parse_args(argv)

    files = iter_python_files(args.paths)
    if not files:
        print("No .py files found.", file=sys.stderr)
        return 1

    all_findings: list[Finding] = []
    for file in files:
        all_findings.extend(scan_file(file))

    if not all_findings:
        print("No known v2 -> kotakneoapi migration issues found.")
        return 0

    for finding in all_findings:
        location = f"{finding.file}:{finding.line}"
        print(f"[{finding.severity.upper()}] {location}: {finding.message}")

    errors = sum(1 for f in all_findings if f.severity == "error")
    warnings = sum(1 for f in all_findings if f.severity == "warning")
    print(f"\n{errors} error(s), {warnings} warning(s) across {len(files)} file(s).")
    print(
        "This tool only reports issues — it does not modify files. "
        "Review each item and update the code by hand."
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
