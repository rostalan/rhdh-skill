## Failure Signatures

## Purpose
Map common symptoms to likely causes and highest-value next diagnostics.

## Signature Matrix
| Symptom | Likely Cause | Next Diagnostic | Action Bias |
|---------|--------------|-----------------|------------|
| `oc whoami` fails | Cluster session/auth issue | Re-login and verify project permissions | Blocker |
| RHDH route missing | Deploy/route creation failure | Inspect deployment status and route events | Blocker |
| Auth endpoint not returning expected redirect | Keycloak route/config mismatch | Verify Keycloak route + realm/env values | Blocker |
| Orchestrator health endpoint not `200` | Orchestrator install/config issue | Review install logs and dependent service readiness | Blocker |
| CSV missing in `openshift-operators` | Subscription/channel/source mismatch | Inspect subscriptions and catalog source | Blocker |
| OSL pre-release target set but subscription/source unresolved | Incomplete pre-release configuration | Validate Subscription, CatalogSource, and CSV resolution | Blocker |
| Works on one target but not another | Dependency drift/compat mismatch | Run dependency context + version matrix check | Risk/Blocker |
| Repeated flaky failures | Non-deterministic environment state | Use recovery-and-rerun controlled reset | Risk |

## Classification Rules
- Treat missing core infrastructure or auth prerequisites as blockers.
- Treat environment flakiness and unresolved compatibility uncertainty as risks until reproducible.
- Escalate to blocker when the same high-severity symptom reproduces after one clean rerun.

## Required Report Fields Per Signature
- observed symptom,
- evidence command/output,
- likely cause hypothesis,
- next diagnostic command,
- decision impact (`blocker` or `risk`).
