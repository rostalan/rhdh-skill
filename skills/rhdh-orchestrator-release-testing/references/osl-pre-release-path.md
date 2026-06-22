## OSL Pre-Release Validation Path

## Purpose

Define an upstream-aligned validation path for OSL release candidates (RC/alpha/beta) before GA.

## When This Applies

Use this path when the target tuple includes an OSL pre-release version (for example `1.3.0-rc.1`). The `release_target.py` script sets `is_pre_release_flow: true` for these targets.

## Upstream Sources of Truth

- RHDH Orchestrator documentation: install/upgrade and operator subscription guidance.
- `rhdh-test-instance` upstream README + Makefile deploy flows (`deploy.sh`, `deploy-operator`, `deploy-helm`).

Avoid relying on local-only helper scripts or unmerged branch conventions.

## Validation Checks

1. Confirm the intended OSL pre-release target (version/channel/starting CSV) is explicitly recorded.
2. Run dependency context check:
   ```bash
   python "$SKILL_DIR/scripts/dependency_context.py" --json
   ```
3. Verify catalog source + subscription resolve to the intended operator package/channel:
   ```bash
   oc get subscription -n openshift-operators -o yaml
   oc get catalogsource -n openshift-marketplace
   ```
4. Verify CSV reaches `Succeeded`:
   ```bash
   oc get csv -n openshift-operators
   ```

## Execution Guidance

Use upstream-supported deployment entry points in `rhdh-test-instance`:

- `./deploy.sh operator <version> --with-orchestrator`
- `make deploy-operator VERSION=<version> ORCH=true`

For quick, non-production infra bootstrapping, Red Hat docs also describe `plugin-infra.sh`; do not treat that as a production path.

## Common Failures

| Symptom | Likely cause |
|---------|-------------|
| CSV not appearing | Catalog source unavailable or package/channel mismatch |
| Wrong operator version installed | Subscription channel/starting CSV mismatch |
| Auth redirect broken after OSL update | Backend auth or OIDC config drift between versions |

## Relationship to Failure Signatures

Map pre-release-specific symptoms through `failure-signatures.md` for structured triage.
