#!/usr/bin/env python3
"""Extract dependency context for RHDH + OSL release validation.

Reads key version files from workspace repos and compares expected vs
actual dependency versions. Produces a delta report used for risk triage.

Exit codes:
  0  context extracted (may include deltas)
  1  extraction failed (missing repos or files)
  2  usage error
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

VERSION_SOURCES = {
    "test-instance-makefile": {
        "description": "rhdh-test-instance Makefile defaults",
        "repo_env": "RHDH_TEST_INSTANCE",
        "file": "Makefile",
        "patterns": {
            "default_namespace": r"^NAMESPACE\s*\?=\s*([^\s#]+)",
            "default_version": r"^VERSION\s*\?=\s*([^\s#]+)",
            "default_orch": r"^ORCH\s*\?=\s*([^\s#]+)",
        },
    },
    "overlay-source-json": {
        "description": "Orchestrator overlay source.json",
        "repo_env": "RHDH_OVERLAY_REPO",
        "file": "workspaces/orchestrator/source.json",
        "patterns": {
            "overlay_repo_ref": r"\"repo-ref\"\s*:\s*\"([^\"]+)\"",
            "overlay_backstage_version": r"\"repo-backstage-version\"\s*:\s*\"([^\"]+)\"",
        },
    },
}


def _read_env_file(path: Path) -> dict[str, str]:
    """Parse a simple KEY=VALUE .env file (no interpolation)."""
    result = {}
    if not path.is_file():
        return result
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'\"")
                result[key] = value
    return result


def _read_patterns(path: Path, patterns: dict[str, str]) -> dict[str, str | None]:
    if not path.is_file():
        return {k: None for k in patterns}
    text = path.read_text(encoding="utf-8")
    result = {}
    for key, pat in patterns.items():
        m = re.search(pat, text, re.MULTILINE)
        result[key] = m.group(1) if m else None
    return result


def extract_source(source_id: str, spec: dict) -> dict:
    repo_path_raw = os.environ.get(spec["repo_env"], "")
    if not repo_path_raw:
        return {
            "source": source_id,
            "description": spec["description"],
            "available": False,
            "error": f"${spec['repo_env']} not set",
            "values": {},
        }

    repo_path = Path(repo_path_raw)
    target_file = repo_path / spec["file"]

    if not target_file.exists():
        return {
            "source": source_id,
            "description": spec["description"],
            "available": False,
            "error": f"File not found: {target_file}",
            "values": {},
        }

    if "keys" in spec:
        env_data = _read_env_file(target_file)
        values = {k: env_data.get(k) for k in spec["keys"]}
    elif "patterns" in spec:
        values = _read_patterns(target_file, spec["patterns"])
    else:
        values = {}

    return {
        "source": source_id,
        "description": spec["description"],
        "available": True,
        "file": str(target_file),
        "values": values,
        "error": None,
    }


def compute_deltas(sources: list[dict]) -> list[dict]:
    """Identify version mismatches across sources."""
    deltas = []
    version_map: dict[str, list[tuple[str, str]]] = {}

    for src in sources:
        if not src["available"]:
            continue
        for key, val in src["values"].items():
            if val is not None:
                version_map.setdefault(key, []).append((src["source"], val))

    for key, entries in version_map.items():
        unique_values = set(v for _, v in entries)
        if len(unique_values) > 1:
            deltas.append({
                "key": key,
                "mismatch": True,
                "values": [{"source": s, "value": v} for s, v in entries],
                "risk": "high" if key in ("RHDH_VERSION", "OSL_VERSION") else "medium",
            })

    return deltas


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract dependency context for RHDH + OSL release validation.",
        epilog="Environment variables:\n"
        "  RHDH_TEST_INSTANCE  Path to rhdh-test-instance checkout\n"
        "  RHDH_OVERLAY_REPO   Path to rhdh-plugin-export-overlays checkout\n"
        "\nExamples:\n"
        "  %(prog)s\n"
        "  %(prog)s --json\n"
        "  %(prog)s --sources test-instance-makefile overlay-source-json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Output as JSON (default when stdout is not a TTY)",
    )
    parser.add_argument(
        "--sources", nargs="*", default=None,
        help="Specific sources to check (default: all)",
    )
    args = parser.parse_args()

    source_ids = args.sources or list(VERSION_SOURCES.keys())
    invalid = [s for s in source_ids if s not in VERSION_SOURCES]
    if invalid:
        print(f"Unknown sources: {', '.join(invalid)}", file=sys.stderr)
        print(f"Available: {', '.join(VERSION_SOURCES.keys())}", file=sys.stderr)
        sys.exit(2)

    sources = []
    for sid in source_ids:
        sources.append(extract_source(sid, VERSION_SOURCES[sid]))

    deltas = compute_deltas(sources)
    unavailable = [s for s in sources if not s["available"]]

    report = {
        "sources": sources,
        "deltas": deltas,
        "has_mismatches": len(deltas) > 0,
        "unavailable_sources": len(unavailable),
        "summary": {
            "total_sources": len(sources),
            "available": len(sources) - len(unavailable),
            "mismatches": len(deltas),
            "high_risk_deltas": len([d for d in deltas if d["risk"] == "high"]),
        },
    }

    use_json = args.json_output or not sys.stdout.isatty()
    if use_json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("=== Dependency Context ===\n")
        for src in sources:
            status = "OK" if src["available"] else "MISSING"
            print(f"  [{status}] {src['description']}")
            if src["available"]:
                for k, v in src["values"].items():
                    print(f"         {k} = {v or '(not set)'}")
            else:
                print(f"         {src['error']}")
            print()

        if deltas:
            print("Mismatches:")
            for d in deltas:
                risk_tag = f"[{d['risk'].upper()}]"
                vals = ", ".join(f"{e['source']}={e['value']}" for e in d["values"])
                print(f"  {risk_tag} {d['key']}: {vals}")
        else:
            print("No version mismatches detected.")

    sys.exit(0)


if __name__ == "__main__":
    main()
