## Debugging Playbook

## Purpose
Provide a deterministic workflow for diagnosing failures in the RHDH + orchestrator + OSL stack.

## Entry Conditions
Use this playbook when:
- setup fails during install or readiness,
- runtime health/auth/workflow behavior is broken,
- reruns are failing without clear cause.

## Fast Triage Flow
1. Confirm target tuple with `release-matrix-selection.md`.
2. Run preflight:
   ```bash
   python "$SKILL_DIR/scripts/prereq_check.py" --json
   ```
3. Capture baseline evidence (routes, pods, events, operator status).
4. Classify failure with `failure-signatures.md`.
5. Run only the next diagnostic indicated by signature mapping.
6. Update decision status (`GO`, `GO_WITH_RISKS`, `NO_GO`) based on evidence.

## Setup Failure Triage
If bring-up fails, inspect in this order:
1. Cluster/session viability (`oc whoami`, project access).
2. Namespace cleanliness and prior resource contamination.
3. Operator/channel/CSV presence and subscription health.
4. RHDH deployment rollout and route resolution.
5. Orchestrator health endpoint and Keycloak auth redirect behavior.

## Runtime Failure Triage
If setup succeeds but behavior is broken, inspect:
1. API health endpoints (`/api/orchestrator/health`, auth endpoints).
2. Workflow resources and dependent services.
3. Dynamic plugin config and effective app config merge.
4. Cross-repo contract mismatches (test-instance vs overlays vs e2e harness).

## Minimal Evidence Commands
```bash
oc get pods -n "$NAMESPACE"
oc get events -n "$NAMESPACE" --sort-by=.lastTimestamp
oc get route -n "$NAMESPACE"
oc get csv -n openshift-operators
oc logs deployment/redhat-developer-hub -n "$NAMESPACE" --tail=200
```

## Decision Guidance
- `NO_GO`: blocker is reproducible and unresolved.
- `GO_WITH_RISKS`: functionality works but confidence gaps remain.
- `GO`: required checks pass and no unresolved blockers/critical risks remain.
