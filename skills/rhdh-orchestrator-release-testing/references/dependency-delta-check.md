## Dependency Delta Check

## Purpose

Identify version mismatches and dependency drift across the repos that must align for a successful orchestrator release validation.

## Key Dependency Surfaces

| Surface | Where defined | What can drift |
|---------|---------------|----------------|
| RHDH deploy target | `rhdh-test-instance/Makefile` defaults and deploy command inputs (`VERSION`, `ORCH`) | Deploy target drift between runs |
| OSL operator target | Operator subscription/package/channel/starting CSV in cluster | Operator channel, catalog source |
| Backstage base version | `rhdh-plugin-export-overlays/workspaces/orchestrator/source.json` (`repo-backstage-version`) | Plugin build compatibility |
| Orchestrator plugin version | Overlay workspace `plugins-list.yaml` | Runtime plugin load, e2e test expectations |
| e2e test harness | `rhdh/e2e-tests/playwright/` and `rhdh-e2e-test-utils/` | Test runner version, page object contracts |

## Extraction

Use `dependency_context.py` to pull current values from workspace repos:

```bash
RHDH_TEST_INSTANCE=/path/to/rhdh-test-instance \
RHDH_OVERLAY_REPO=/path/to/rhdh-plugin-export-overlays \
python "$SKILL_DIR/scripts/dependency_context.py" --json
```

The script reports mismatches automatically for the repo-backed inputs. Resolve any high-risk delta before proceeding.

## Risk Classification

| Delta type | Risk | Action |
|------------|------|--------|
| RHDH version mismatch across repos | High | Align before testing — wrong version invalidates results |
| OSL operator target mismatch | High | Verify subscription package/channel/starting CSV against intended RC |
| Backstage base version drift | Medium | Check overlay `source.json` (`repo-backstage-version`) against rhdh repo expectations |
| Plugin version drift | Medium | May cause runtime load failures — check overlay build status |
| e2e harness contract mismatch | Low-Medium | Test may fail but can be triaged separately |

## When to Run

- Before every validation run (part of prerequisites).
- After updating any version in any repo.
- When a failure has no obvious cause — dependency drift is a common hidden root cause.

## Cross-Reference

For repo locations and relationships, see `../../rhdh/references/rhdh-repos.md`.
