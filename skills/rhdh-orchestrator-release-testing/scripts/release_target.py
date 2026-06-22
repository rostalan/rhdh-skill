#!/usr/bin/env python3
"""Normalize and validate an RHDH + OSL release target tuple.

Accepts version strings in various formats and produces a canonical
target tuple used by downstream scripts and validation workflows.

Exit codes:
  0  valid target tuple produced
  1  validation failure (missing or incompatible versions)
  2  usage error
"""

import argparse
import json
import re
import sys
from pathlib import Path

KNOWN_INSTALL_MODES = ("helm", "operator")

RHDH_VERSION_RE = re.compile(r"^(\d+)\.(\d+)(?:\.(\d+))?$")
OSL_VERSION_RE = re.compile(
    r"^(\d+)\.(\d+)(?:\.(\d+))?(?:-(rc|alpha|beta)\.?(\d+))?$"
)


def parse_rhdh_version(raw: str) -> dict | None:
    m = RHDH_VERSION_RE.match(raw.strip())
    if not m:
        return None
    major, minor, patch = m.group(1), m.group(2), m.group(3)
    return {
        "raw": raw.strip(),
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch) if patch else None,
        "normalized": f"{major}.{minor}" + (f".{patch}" if patch else ""),
    }


def parse_osl_version(raw: str) -> dict | None:
    m = OSL_VERSION_RE.match(raw.strip())
    if not m:
        return None
    major, minor, patch = m.group(1), m.group(2), m.group(3)
    pre_label, pre_num = m.group(4), m.group(5)
    normalized = f"{major}.{minor}"
    if patch:
        normalized += f".{patch}"
    if pre_label:
        normalized += f"-{pre_label}"
        if pre_num:
            normalized += f".{pre_num}"
    return {
        "raw": raw.strip(),
        "major": int(major),
        "minor": int(minor),
        "patch": int(patch) if patch else None,
        "pre_release": pre_label,
        "pre_release_num": int(pre_num) if pre_num else None,
        "is_pre_release": pre_label is not None,
        "normalized": normalized,
    }


def build_target(
    rhdh_version: str,
    install_mode: str,
    osl_version: str | None = None,
) -> dict:
    errors: list[str] = []

    rhdh = parse_rhdh_version(rhdh_version)
    if not rhdh:
        errors.append(
            f"Invalid RHDH version '{rhdh_version}'. Expected: MAJOR.MINOR[.PATCH]"
        )

    mode = install_mode.lower().strip()
    if mode not in KNOWN_INSTALL_MODES:
        errors.append(
            f"Unknown install mode '{install_mode}'. Expected: {', '.join(KNOWN_INSTALL_MODES)}"
        )

    osl = None
    if osl_version:
        osl = parse_osl_version(osl_version)
        if not osl:
            errors.append(
                f"Invalid OSL version '{osl_version}'. "
                "Expected: MAJOR.MINOR[.PATCH][-rc.N|-alpha.N|-beta.N]"
            )

    if errors:
        return {"valid": False, "errors": errors}

    target = {
        "valid": True,
        "rhdh": rhdh,
        "install_mode": mode,
        "osl": osl,
        "is_pre_release_flow": osl is not None and osl.get("is_pre_release", False),
        "tuple_key": _tuple_key(rhdh, mode, osl),
    }
    return target


def _tuple_key(
    rhdh: dict, mode: str, osl: dict | None
) -> str:
    key = f"rhdh-{rhdh['normalized']}_{mode}"
    if osl:
        key += f"_osl-{osl['normalized']}"
    return key


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize an RHDH + OSL release target tuple.",
        epilog="Examples:\n"
        "  %(prog)s 1.4 helm\n"
        "  %(prog)s 1.4.1 operator --osl 1.3.0-rc.1\n"
        "  %(prog)s 1.4 helm --json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("rhdh_version", help="RHDH version (e.g. 1.4 or 1.4.1)")
    parser.add_argument("install_mode", help="Install mode: helm or operator")
    parser.add_argument(
        "--osl", dest="osl_version", default=None,
        help="OSL version to target (e.g. 1.3.0, 1.3.0-rc.1)",
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Output as JSON (default when stdout is not a TTY)",
    )
    args = parser.parse_args()

    target = build_target(args.rhdh_version, args.install_mode, args.osl_version)

    use_json = args.json_output or not sys.stdout.isatty()
    if use_json:
        json.dump(target, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        if not target["valid"]:
            for err in target["errors"]:
                print(f"ERROR: {err}", file=sys.stderr)
        else:
            print(f"Target:    {target['tuple_key']}")
            print(f"RHDH:      {target['rhdh']['normalized']}")
            print(f"Mode:      {target['install_mode']}")
            if target["osl"]:
                print(f"OSL:       {target['osl']['normalized']}")
                if target["is_pre_release_flow"]:
                    print("Flow:      OSL pre-release")

    sys.exit(0 if target["valid"] else 1)


if __name__ == "__main__":
    main()
