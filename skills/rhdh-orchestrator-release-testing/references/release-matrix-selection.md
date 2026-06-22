## Release Matrix Selection

## Purpose

Define how to normalize, validate, and select the RHDH + OSL target tuple for a release validation run.

## Target Tuple

Every validation run targets a specific combination:

| Field | Required | Example | Source |
|-------|----------|---------|--------|
| RHDH version | yes | `1.4`, `1.4.1` | User input or release schedule |
| Install mode | yes | `helm`, `operator` | User input |
| OSL version | no | `1.3.0`, `1.3.0-rc.1` | User input or release candidate target |

Use the `release_target.py` script for normalization:

```bash
python "$SKILL_DIR/scripts/release_target.py" 1.4 helm --osl 1.3.0-rc.1 --json
```

## Install Mode Rules

| Mode | When to use | Deployment method |
|------|-------------|-------------------|
| `helm` | Default for most QE runs | Helm chart via `deploy.sh` or `helm/deploy.sh` in `rhdh-test-instance` |
| `operator` | Operator-specific validation path | Operator install/deploy via `install-operator.sh`, `operator/deploy.sh`, or `deploy.sh operator ...` in `rhdh-test-instance` |

## Matrix Expansion

For full release readiness, validate all supported combinations:

```
RHDH_VERSION x INSTALL_MODE [x OSL_VERSION]
```

If OSL version is not specified, use the default supported channel for the selected RHDH release. When an explicit OSL pre-release is provided, follow the upstream OSL pre-release validation procedure in `osl-pre-release-path.md`.

## Version Compatibility

Cross-reference RHDH and OSL versions against the version matrix in `../../rhdh/references/versions.md`. If the requested combination is not in the matrix, flag it as a risk and confirm with the user before proceeding.

## Selecting Targets for a Release

1. Identify the RHDH version under release.
2. Determine which install modes are in scope (typically both).
3. Check if a new OSL RC is available — if so, add the pre-release tuple.
4. Normalize all tuples via `release_target.py`.
5. Run prerequisites for each tuple before proceeding.
