#!/usr/bin/env python3
"""Check prerequisites for RHDH + Orchestrator release testing.

Validates that required CLI tools, cluster access, and environment
variables are present before starting a release validation workflow.

Exit codes:
  0  all prerequisites met
  1  one or more prerequisites failed
  2  usage error
"""

import argparse
import json
import os
import shutil
import subprocess
import sys


def _run(cmd: list[str], timeout: int = 15) -> tuple[int, str, str]:
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=(sys.platform == "win32"),
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Command not found: {cmd[0]}"
    except subprocess.TimeoutExpired:
        return 124, "", f"Command timed out after {timeout}s: {' '.join(cmd)}"


def check_tool(name: str, version_flag: str = "--version") -> dict:
    path = shutil.which(name)
    if not path:
        return {
            "name": name,
            "available": False,
            "error": f"'{name}' not found on PATH",
        }
    rc, stdout, stderr = _run([name, version_flag])
    version = stdout or stderr
    return {
        "name": name,
        "available": rc == 0,
        "version": version.split("\n")[0] if version else "unknown",
        "path": path,
        "error": None if rc == 0 else f"Exit code {rc}: {stderr}",
    }


def check_cluster_access() -> dict:
    rc, stdout, stderr = _run(["oc", "whoami"])
    if rc != 0:
        return {
            "name": "cluster_access",
            "available": False,
            "error": "Not logged into an OpenShift cluster. Run 'oc login' first.",
        }
    rc2, server, _ = _run(["oc", "whoami", "--show-server"])
    return {
        "name": "cluster_access",
        "available": True,
        "user": stdout,
        "server": server if rc2 == 0 else "unknown",
        "error": None,
    }


def check_env_var(name: str, required: bool = True) -> dict:
    value = os.environ.get(name)
    return {
        "name": name,
        "available": value is not None,
        "set": value is not None,
        "required": required,
        "error": f"Environment variable '{name}' is not set" if required and not value else None,
    }


def check_repo_path(name: str, env_var: str, subpath: str | None = None) -> dict:
    """Check that a workspace repo path is set and the directory exists."""
    from pathlib import Path

    raw = os.environ.get(env_var, "")
    if not raw:
        return {
            "name": name,
            "available": False,
            "error": f"${env_var} is not set. Point it to your local checkout.",
        }
    p = Path(raw)
    if not p.is_dir():
        return {
            "name": name,
            "available": False,
            "path": raw,
            "error": f"${env_var}={raw} does not exist or is not a directory.",
        }
    if subpath and not (p / subpath).exists():
        return {
            "name": name,
            "available": False,
            "path": raw,
            "error": f"Expected '{subpath}' not found under ${env_var}={raw}.",
        }
    return {"name": name, "available": True, "path": raw, "error": None}


def run_checks(include_cluster: bool = True) -> dict:
    results: list[dict] = []

    tool_version_flags = {
        "oc": "version",
        "helm": "version",
        "kubectl": "version",
        "git": "--version",
        "python3": "--version",
    }
    for tool, flag in tool_version_flags.items():
        results.append(check_tool(tool, version_flag=flag))

    if include_cluster:
        results.append(check_cluster_access())

    results.append(check_env_var("NAMESPACE", required=False))
    results.append(check_env_var("REDHAT_WORKSPACE", required=False))

    passed = [r for r in results if r["available"]]
    failed = [r for r in results if not r["available"] and r.get("required", True)]
    warnings = [r for r in results if not r["available"] and not r.get("required", True)]

    all_ok = len(failed) == 0
    return {
        "all_passed": all_ok,
        "total": len(results),
        "passed": len(passed),
        "failed": len(failed),
        "warnings": len(warnings),
        "checks": results,
        "blockers": [r["error"] for r in failed if r.get("error")],
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check prerequisites for RHDH + Orchestrator release testing.",
        epilog="Examples:\n"
        "  %(prog)s\n"
        "  %(prog)s --json\n"
        "  %(prog)s --skip-cluster\n",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--json", dest="json_output", action="store_true",
        help="Output as JSON (default when stdout is not a TTY)",
    )
    parser.add_argument(
        "--skip-cluster", action="store_true",
        help="Skip cluster access check (for offline prereq validation)",
    )
    args = parser.parse_args()

    report = run_checks(include_cluster=not args.skip_cluster)

    use_json = args.json_output or not sys.stdout.isatty()
    if use_json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        print("=== Prerequisite Check ===\n")
        for check in report["checks"]:
            status = "PASS" if check["available"] else "FAIL"
            marker = "\u2713" if check["available"] else "\u2717"
            line = f"  {marker} [{status}] {check['name']}"
            if check.get("version"):
                line += f" ({check['version']})"
            if check.get("user"):
                line += f" (user={check['user']})"
            if check.get("error") and not check["available"]:
                line += f"\n           {check['error']}"
            print(line)

        print(f"\nResult: {report['passed']}/{report['total']} passed", end="")
        if report["warnings"]:
            print(f", {report['warnings']} warnings", end="")
        print()
        if not report["all_passed"]:
            print("\nBlockers:")
            for b in report["blockers"]:
                print(f"  - {b}")

    sys.exit(0 if report["all_passed"] else 1)


if __name__ == "__main__":
    main()
