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
        "isVerify",
    },
    "cancel_order": set(),  # amo/isVerify both kept; no drops.
    "trade_report": {"order_id"},  # trade_report() now takes no filter.
    "limits": {"segment", "exchange", "product"},  # limits() now takes none.
    "margin_required": set(),  # signature unchanged between versions.
}

# Values that v2 silently resolved to a canonical code but kotakneoapi now
# rejects outright (ApiValueError), for parameters checked by string-literal
# value rather than by keyword name. Keyed by (method, parameter) so the same
# parameter name in a different method isn't checked against the wrong set.
# Only exact literal matches are checked — this can't see values computed at
# runtime (f-strings, variables, config lookups).
REMOVED_LITERAL_VALUES: dict[tuple[str, str], dict[str, str]] = {
    ("place_order", "exchange_segment"): {
        v: (
            f"'{v}' is no longer resolved to a canonical exchange segment in "
            "kotakneoapi — only the exact codes nse_cm, bse_cm, nse_fo, "
            "bse_fo, mcx_fo are accepted. Generic aliases are rejected "
            "because they're ambiguous (e.g. 'BSE' could mean bse_cm or "
            "bse_fo)."
        )
        for v in ("NSE", "nse", "BSE", "bse", "NFO", "nfo", "BFO", "bfo", "MCX", "mcx")
    }
    | {
        v: (
            f"'{v}' (currency derivatives) is not accepted by place_order in "
            "kotakneoapi at all — this segment isn't supported for order "
            "placement, under any spelling."
        )
        for v in ("CDS", "cds", "cde_fo", "BCD", "bcd", "bcs-fo")
    },
    ("place_order", "product"): {
        v: (
            f"'{v}' is no longer accepted by place_order in kotakneoapi — "
            "only the exact codes CNC, NRML, MIS, MTF are accepted. Bracket "
            "(BO) and Cover (CO) orders are no longer supported at all; "
            "other aliases (e.g. 'Normal', 'Cash and Carry') are rejected, "
            "not resolved."
        )
        for v in (
            "Normal",
            "INTRADAY",
            "intraday",
            "CO",
            "co",
            "Cover Order",
            "BO",
            "bo",
            "Bracket Order",
        )
    },
    ("place_order", "order_type"): {
        v: (
            f"'{v}' is no longer resolved to a canonical order type in "
            "kotakneoapi — only the exact codes L, MKT, SL, SL-M are "
            "accepted. Multi-leg types (Spread/2L/3L) are no longer "
            "supported at all."
        )
        for v in (
            "Limit",
            "Market",
            "Stop loss limit",
            "Stop loss market",
            "Spread",
            "SP",
            "sp",
            "2L",
            "2l",
            "Two Leg",
            "3L",
            "3l",
            "Three leg",
        )
    },
    ("place_order", "validity"): {
        v: (
            f"'{v}' is no longer accepted by place_order in kotakneoapi — "
            "only DAY and IOC are accepted (DAY only for mcx_fo)."
        )
        for v in ("GTC", "EOS", "GTD")
    },
    ("modify_order", "order_type"): {
        v: (
            f"'{v}' is no longer resolved to a canonical order type in "
            "kotakneoapi — only the exact codes L, MKT, SL, SL-M are "
            "accepted."
        )
        for v in ("Limit", "Market", "Stop loss limit", "Stop loss market")
    },
    ("modify_order", "validity"): {
        v: (
            f"'{v}' is no longer accepted by modify_order in kotakneoapi — "
            "only DAY and IOC are accepted."
        )
        for v in ("GTC", "EOS", "GTD")
    },
    ("margin_required", "exchange_segment"): {
        v: (
            f"'{v}' is no longer resolved to a canonical exchange segment by "
            "margin_required in kotakneoapi — only nse_cm, bse_cm, nse_fo, "
            "bse_fo, mcx_fo are accepted."
        )
        for v in ("NSE", "nse", "BSE", "bse", "NFO", "nfo", "BFO", "bfo", "MCX", "mcx")
    },
    ("margin_required", "order_type"): {
        v: (
            f"'{v}' is no longer resolved to a canonical order type by "
            "margin_required in kotakneoapi — only L, MKT, SL, SL-M are "
            "accepted."
        )
        for v in ("Limit", "Market")
    },
}

# (order_type_param, price_param) pairs, keyed by method, where price="0" (or
# blank) used to reach the exchange for L/SL orders and is now rejected
# client-side. Only checked when order_type is a literal in this set AND
# price is a literal "0" in the same call.
ZERO_PRICE_REJECTED_ORDER_TYPES = {"L", "SL"}
ZERO_PRICE_NOTE = (
    "price=\"0\" is no longer accepted for order_type '{order_type}' in "
    "kotakneoapi — L/SL orders now require a real positive price "
    "client-side (previously this reached the exchange and could result in "
    "an unintended fill at a nonsense price). MKT/SL-M orders are "
    "unaffected."
)

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

# Top-level classes exported by v2's neo_api_client package that don't exist
# in kotakneoapi at all — importing any of these raises ImportError.
REMOVED_IMPORTS: dict[str, str] = {
    "NeoWebSocket": (
        "Removed in kotakneoapi — importing this raises ImportError. It was "
        "the low-level callback-based WebSocket class; use the async "
        "SFeedWebSocket instead, e.g. `client.create_websocket()` (see "
        "neo_api_client.websocket.feed.SFeedWebSocket)."
    ),
    "HSWebSocket": (
        "Removed in kotakneoapi — importing this raises ImportError. It was "
        "part of the legacy low-level WebSocket implementation with no "
        "direct replacement; use the async SFeedWebSocket via "
        "`client.create_websocket()` instead."
    ),
    "HSIWebSocket": (
        "Removed in kotakneoapi — importing this raises ImportError. It was "
        "part of the legacy low-level WebSocket implementation with no "
        "direct replacement; use the async SFeedWebSocket via "
        "`client.create_websocket()` instead."
    ),
}

# NeoAPI attributes that existed in v2 to hold WebSocket callbacks. In
# kotakneoapi they're still initialized to None in __init__ (so assigning to
# them doesn't raise), but nothing ever reads them again — the async
# SFeedWebSocket/OrderFeedWebSocket clients don't use this callback pattern
# at all. Assigning to these is a silent no-op, not an error, which is worse
# than a crash for migration purposes.
LEGACY_CALLBACK_ATTRS = {"on_message", "on_error", "on_open", "on_close"}
LEGACY_CALLBACK_NOTE = (
    "Assigning to `{attr}` is a silent no-op in kotakneoapi — this attribute "
    "is still initialized to None but nothing reads it anymore (the legacy "
    "callback-based WebSocket was replaced by the async SFeedWebSocket / "
    "OrderFeedWebSocket clients). Your callback will never be called. "
    "Migrate to `async with client.create_websocket() as ws:` / "
    "`async for message in ws:` instead."
)

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


def _kwarg_literal_strings(node: ast.Call) -> dict[str, str]:
    """Map keyword-argument name to its value, for string-literal values only."""
    values = {}
    for kw in node.keywords:
        if (
            kw.arg is not None
            and isinstance(kw.value, ast.Constant)
            and isinstance(kw.value.value, str)
        ):
            values[kw.arg] = kw.value.value
    return values


class MigrationVisitor(ast.NodeVisitor):
    # Method names are matched regardless of the receiver, since resolving
    # "is this variable actually a NeoAPI instance" reliably would need type
    # inference this tool doesn't do. This can over-report on unrelated
    # objects that happen to share a method name (e.g. some other class's
    # own `subscribe()`) — read findings with that in mind.

    def __init__(self, file: Path) -> None:
        self.file = file
        self.findings: list[Finding] = []

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module == "neo_api_client":
            for alias in node.names:
                if alias.name in REMOVED_IMPORTS:
                    self.findings.append(
                        Finding(
                            self.file,
                            node.lineno,
                            "error",
                            f"import {alias.name}: {REMOVED_IMPORTS[alias.name]}",
                        )
                    )
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        if (
            node.attr in LEGACY_CALLBACK_ATTRS
            and isinstance(node.ctx, ast.Store)
            and isinstance(node.value, ast.Name)
        ):
            self.findings.append(
                Finding(
                    self.file,
                    node.lineno,
                    "warning",
                    f"{node.value.id}.{node.attr} = ...: "
                    + LEGACY_CALLBACK_NOTE.format(attr=node.attr),
                )
            )
        self.generic_visit(node)

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

        if name is not None and isinstance(node.func, ast.Attribute):
            literals = _kwarg_literal_strings(node)

            for param, value in literals.items():
                removed = REMOVED_LITERAL_VALUES.get((name, param))
                if removed and value in removed:
                    self.findings.append(
                        Finding(
                            self.file,
                            node.lineno,
                            "error",
                            f'{name}({param}="{value}", ...): {removed[value]}',
                        )
                    )

            if name in {"place_order", "modify_order"}:
                order_type = literals.get("order_type")
                price = literals.get("price")
                if (
                    order_type in ZERO_PRICE_REJECTED_ORDER_TYPES
                    and price is not None
                    and price.strip() in ("", "0", "0.0")
                ):
                    self.findings.append(
                        Finding(
                            self.file,
                            node.lineno,
                            "error",
                            f'{name}(order_type="{order_type}", price="{price}", ...): '
                            + ZERO_PRICE_NOTE.format(order_type=order_type),
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
