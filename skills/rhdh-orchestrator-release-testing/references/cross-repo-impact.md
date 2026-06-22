## Cross-Repo Impact Analysis

## Purpose

Map the repos involved in an orchestrator release validation and identify where contract mismatches cause test failures.

## Repo Dependency Graph

```
rhdh-test-instance
  ├── deploys RHDH (helm chart or operator)
  ├── configures OSL (operator subscription + catalog source)
  └── references rhdh-plugin-export-overlays (dynamic plugin config)

rhdh-plugin-export-overlays
  ├── builds orchestrator plugin overlays
  ├── depends on upstream backstage version (`workspaces/orchestrator/source.json`)
  └── produces OCI artifacts consumed by RHDH at runtime

rhdh (main repo)
  ├── contains e2e tests (playwright)
  └── references rhdh-e2e-test-utils for shared pages/helpers

rhdh-e2e-test-utils
  ├── shared Playwright pages (orchestrator.ts)
  └── shared helpers (kubernetes-client.ts)
```

## Contract Surfaces

| Surface | Producer | Consumer | Break symptom |
|---------|----------|----------|---------------|
| Helm chart version/tag | rhdh release | rhdh-test-instance deploy.sh | Wrong RHDH version deployed |
| Operator CSV version | OSL release pipeline | rhdh-test-instance operator deployment (`deploy.sh operator ... --with-orchestrator`) | Operator install fails or wrong version |
| Plugin OCI artifact | rhdh-plugin-export-overlays CI | RHDH runtime (dynamic-plugins.yaml) | Plugin fails to load at startup |
| Orchestrator page selectors | rhdh-e2e-test-utils orchestrator.ts | e2e test suites | Tests fail on element-not-found |
| Kubernetes client helpers | rhdh-e2e-test-utils kubernetes-client.ts | e2e test suites | Setup/teardown failures |
| App config shape | rhdh (app-config.yaml templates) | rhdh-test-instance (rhdh-app-config.yaml) | Config merge failures at startup |

## Impact Check Procedure

1. For each repo in the dependency graph, check the branch and most recent commit:
   ```bash
   for repo in rhdh-test-instance rhdh-plugin-export-overlays rhdh rhdh-e2e-test-utils; do
     echo "--- $repo ---"
     git -C "$REDHAT_WORKSPACE/$repo" log --oneline -3
     git -C "$REDHAT_WORKSPACE/$repo" branch --show-current
   done
   ```

2. Compare expected versions (from the target tuple) against what each repo provides.

3. Flag any repo on a feature branch or with uncommitted changes — these introduce non-reproducibility.

## When Contracts Break

Cross-repo contract mismatches are the most common hidden cause of "works in one environment, fails in another." The dependency context script catches version-level drift, but contract-level mismatches (page selector changes, config shape changes) require manual inspection or e2e test execution.

## Risk Mitigation

- Pin repos to tagged releases or specific commits for reproducibility.
- Run the full dependency context check before every validation.
- When a contract surface changes in one repo, check all consumers.

## Cross-Reference

For the full repo map and key paths, see `../../rhdh/references/rhdh-repos.md`.
For test locations, see the workspace map in the root `AGENTS.md`.
