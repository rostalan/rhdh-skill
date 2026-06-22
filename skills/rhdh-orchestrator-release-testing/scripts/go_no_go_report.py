#!/usr/bin/env python3
"""Generate a structured go/no-go report for RHDH + Orchestrator release testing.

Accepts blockers, risks, and evidence items as JSON input (stdin or file)
and produces a formatted decision report.

Exit codes:
  0  report generated
  1  input validation failed
  2  usage error
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

VALID_DECISIONS = ("GO", "GO_WITH_RISKS", "NO_GO")

REPORT_SCHEMA = {
    "required_fields": ["decision", "target", "blockers", "risks", "next_actions"],
    "optional_fields": ["evidence", "notes", "timestamp", "prereq_summary"],
}


def validate_input(data: dict) -> list[str]:
    errors = []
    for field in REPORT_SCHEMA["required_fields"]:
        if field not in data:
            errors.append(f"Missing required field: '{field}'")

    if "decision" in data and data["decision"] not in VALID_DECISIONS:
        errors.append(
            f"Invalid decision '{data['decision']}'. "
            f"Must be one of: {', '.join(VALID_DECISIONS)}"
        )

    for list_field in ("blockers", "risks", "next_actions"):
        if list_field in data and not isinstance(data[list_field], list):
            errors.append(f"'{list_field}' must be a list")

    if "target" in data and not isinstance(data["target"], dict):
        errors.append("'target' must be an object with rhdh/install_mode/osl fields")

    return errors


def derive_decision(blockers: list, risks: list) -> str:
    if blockers:
        return "NO_GO"
    if risks:
        return "GO_WITH_RISKS"
    return "GO"


def format_markdown(report: dict) -> str:
    lines = []
    ts = report.get("timestamp", datetime.now(timezone.utc).isoformat())
    target = report.get("target", {})
    decision = report["decision"]

    lines.append(f"# Go/No-Go Report")
    lines.append(f"")
    lines.append(f"**Decision: {decision}**")
    lines.append(f"")
    lines.append(f"| Field | Value |")
    lines.append(f"|-------|-------|")
    lines.append(f"| Timestamp | {ts} |")
    if target:
        lines.append(f"| RHDH Version | {target.get('rhdh', 'N/A')} |")
        lines.append(f"| Install Mode | {target.get('install_mode', 'N/A')} |")
        if target.get("osl"):
            lines.append(f"| OSL Version | {target['osl']} |")
    lines.append(f"")

    if report.get("prereq_summary"):
        ps = report["prereq_summary"]
        lines.append(f"## Prerequisites")
        lines.append(f"")
        lines.append(f"Passed: {ps.get('passed', '?')}/{ps.get('total', '?')}")
        if ps.get("blockers"):
            for b in ps["blockers"]:
                lines.append(f"- BLOCKER: {b}")
        lines.append(f"")

    lines.append(f"## Blockers ({len(report.get('blockers', []))})")
    lines.append(f"")
    if report.get("blockers"):
        for i, b in enumerate(report["blockers"], 1):
            if isinstance(b, dict):
                lines.append(f"{i}. **{b.get('title', 'Untitled')}**")
                if b.get("evidence"):
                    lines.append(f"   Evidence: {b['evidence']}")
                if b.get("impact"):
                    lines.append(f"   Impact: {b['impact']}")
            else:
                lines.append(f"{i}. {b}")
    else:
        lines.append("None")
    lines.append(f"")

    lines.append(f"## Risks ({len(report.get('risks', []))})")
    lines.append(f"")
    if report.get("risks"):
        for i, r in enumerate(report["risks"], 1):
            if isinstance(r, dict):
                severity = r.get("severity", "medium").upper()
                lines.append(f"{i}. [{severity}] **{r.get('title', 'Untitled')}**")
                if r.get("mitigation"):
                    lines.append(f"   Mitigation: {r['mitigation']}")
            else:
                lines.append(f"{i}. {r}")
    else:
        lines.append("None")
    lines.append(f"")

    lines.append(f"## Next Actions ({len(report.get('next_actions', []))})")
    lines.append(f"")
    if report.get("next_actions"):
        for i, a in enumerate(report["next_actions"], 1):
            if isinstance(a, dict):
                owner = a.get("owner", "unassigned")
                lines.append(f"{i}. {a.get('action', 'TBD')} (owner: {owner})")
            else:
                lines.append(f"{i}. {a}")
    else:
        lines.append("None")
    lines.append(f"")

    if report.get("evidence"):
        lines.append(f"## Evidence Bundle")
        lines.append(f"")
        for item in report["evidence"]:
            if isinstance(item, dict):
                lines.append(f"- **{item.get('type', 'artifact')}**: {item.get('description', '')}")
                if item.get("path"):
                    lines.append(f"  Path: `{item['path']}`")
            else:
                lines.append(f"- {item}")
        lines.append(f"")

    if report.get("notes"):
        lines.append(f"## Notes")
        lines.append(f"")
        lines.append(report["notes"])
        lines.append(f"")

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a go/no-go report for RHDH + Orchestrator release testing.",
        epilog="Input JSON schema:\n"
        '  {"decision": "GO|GO_WITH_RISKS|NO_GO",\n'
        '   "target": {"rhdh": "1.4", "install_mode": "helm", "osl": "1.3.0"},\n'
        '   "blockers": [...], "risks": [...], "next_actions": [...]}\n'
        "\nExamples:\n"
        "  echo '{...}' | %(prog)s\n"
        "  %(prog)s --input report-data.json\n"
        "  %(prog)s --input report-data.json --format markdown\n"
        "  %(prog)s --auto-decision --input findings.json\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--input", "-i", dest="input_file", default=None,
        help="Path to JSON input file (default: read from stdin)",
    )
    parser.add_argument(
        "--format", "-f", dest="output_format", default="json",
        choices=("json", "markdown"),
        help="Output format (default: json)",
    )
    parser.add_argument(
        "--auto-decision", action="store_true",
        help="Derive decision from blockers/risks if not explicitly set",
    )
    parser.add_argument(
        "--output", "-o", dest="output_file", default=None,
        help="Write output to file instead of stdout",
    )
    args = parser.parse_args()

    if args.input_file:
        try:
            data = json.loads(Path(args.input_file).read_text(encoding="utf-8"))
        except (json.JSONDecodeError, FileNotFoundError, OSError) as e:
            print(f"Failed to read input: {e}", file=sys.stderr)
            sys.exit(2)
    else:
        if sys.stdin.isatty():
            print("Provide JSON input via stdin or --input file.", file=sys.stderr)
            sys.exit(2)
        try:
            data = json.load(sys.stdin)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON input: {e}", file=sys.stderr)
            sys.exit(1)

    if args.auto_decision and "decision" not in data:
        data["decision"] = derive_decision(
            data.get("blockers", []), data.get("risks", [])
        )

    errors = validate_input(data)
    if errors:
        for e in errors:
            print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

    data.setdefault("timestamp", datetime.now(timezone.utc).isoformat())

    if args.output_format == "markdown":
        output = format_markdown(data)
    else:
        output = json.dumps(data, indent=2) + "\n"

    if args.output_file:
        Path(args.output_file).write_text(output, encoding="utf-8")
        print(f"Report written to {args.output_file}", file=sys.stderr)
    else:
        sys.stdout.write(output)

    sys.exit(0)


if __name__ == "__main__":
    main()
