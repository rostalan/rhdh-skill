## Evidence Collection

## Purpose
Define a repeatable diagnostics bundle for triage, escalation, and rerun planning.

## Collection Order
1. Environment identity and target tuple.
2. Cluster object state.
3. Runtime logs and endpoint checks.
4. OSL-specific overrides and env chain.
5. Cross-repo assumption checks.

## Required Bundle Contents
### 1) Context
- target version/install mode/OSL override,
- namespace and cluster identity,
- timestamp window of failure.

### 2) Cluster State
```bash
oc get pods -n "$NAMESPACE" -o wide
oc get events -n "$NAMESPACE" --sort-by=.lastTimestamp
oc get route -n "$NAMESPACE"
oc get subscriptions -n openshift-operators
oc get csv -n openshift-operators
```

### 3) Application and Orchestrator Signals
```bash
oc logs deployment/redhat-developer-hub -n "$NAMESPACE" --tail=400
curl -sk "https://$RHDH_HOST/api/orchestrator/health"
curl -sk -D - -o /dev/null "https://$RHDH_HOST/api/auth/oidc/start?env=production"
```

### 4) OSL Chain Evidence (when pre-release is targeted)
- intended operator package/channel/starting CSV,
- effective Subscription and CatalogSource from cluster,
- resulting CSV version and phase.

### 5) Cross-repo Contract Evidence
- `rhdh-test-instance` deploy command + flags in use,
- `rhdh-e2e-test-utils` script paths availability,
- overlays expectation alignment (where relevant).

## Packaging Guidance
- Prefer plain text snippets with command + output + short interpretation.
- Keep each artifact linked to a failure signature.
- Avoid large unfiltered logs; include targeted excerpts with timestamps.
