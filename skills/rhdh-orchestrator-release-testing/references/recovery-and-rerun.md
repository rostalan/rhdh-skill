## Recovery and Rerun

## Purpose
Provide safe reset and controlled rerun guidance when failures persist.

## When to Use
- same failure repeats across reruns,
- environment contamination is suspected,
- operator/resource leftovers invalidate confidence.

## Recovery Strategy
1. Preserve evidence first (`evidence-collection.md`).
2. Identify whether cleanup can be scoped or must be full.
3. Perform cleanup once, then rerun once with explicit tuple and logging.
4. If failure reproduces, stop rerunning and classify as blocker.

## Cleanup Levels
### Scoped Cleanup
Use when issue appears namespace-local.

```bash
./cleanup.sh --namespace "$NAMESPACE"
```

### Full Orchestrator/Operator Cleanup
Use when operator/catalog/subscription state is likely contaminated.

```bash
./cleanup.sh --namespace "$NAMESPACE" --include-operators --delete-namespace
```

## Controlled Rerun Requirements
- explicit target tuple (`target`, `install_mode`, optional `osl_release`),
- prerequisites re-checked,
- evidence capture commands prepared before rerun,
- no silent changes between attempts.

## Stop Conditions
- two equivalent failures after clean rerun -> `NO_GO`,
- missing mandatory evidence after rerun -> `NO_GO`,
- setup passes but unresolved high-risk drift remains -> `GO_WITH_RISKS`.
