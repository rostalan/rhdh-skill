---
name: rhdh-orchestrator-release-testing
description: >-
  Validates full-stack RHDH + Orchestrator + OSL release readiness and produces
  go/no-go decisions with structured evidence. Use when asked to validate
  orchestrator setup for a release, check orchestrator release readiness,
  run dependency delta analysis, validate a new OSL release candidate,
  prepare for orchestrator QE testing, check RHDH + OSL version compatibility,
  generate a go/no-go report, triage orchestrator test failures, or any
  question about orchestrator release testing, pre-release validation, or
  orchestrator e2e readiness. Also use for
  "dependency delta", "release target normalization", or "cross-repo impact."
---

<cli_setup>

**Derive portable path variables from this SKILL.md location:**

When this file loads, note its absolute path and set:

```bash
SKILL_DIR="$(cd "$(dirname "$0")" && pwd)"   # directory containing SKILL.md
```

If SKILL.md is at `/path/to/skills/rhdh-orchestrator-release-testing/SKILL.md`, then:
- Scripts are at `$SKILL_DIR/scripts/`
- References are at `$SKILL_DIR/references/`

For cross-repo access, use `$REDHAT_WORKSPACE` (defaults to parent of the rhdh-skill checkout) or resolve from `../../rhdh/references/rhdh-repos.md`.

</cli_setup>

<essential_principles>

<principle name="output_contract">
Every validation run MUST produce a structured decision:

| Field | Required | Type |
|-------|----------|------|
| `decision` | yes | `GO`, `GO_WITH_RISKS`, or `NO_GO` |
| `target` | yes | Normalized tuple from `release_target.py` |
| `blockers` | yes | List (empty if none) |
| `risks` | yes | List (empty if none) |
| `next_actions` | yes | List of follow-up steps |
| `evidence` | recommended | Links/snippets supporting the decision |

Use `go_no_go_report.py` to format the final report. Derive the decision from evidence — never guess.
</principle>

<principle name="evidence_first">
Do not declare GO, GO_WITH_RISKS, or NO_GO without concrete evidence.
Every blocker needs a reproducible symptom and diagnostic output.
Every risk needs a stated confidence gap and mitigation path.
Absence of evidence is not evidence of absence — untested areas are risks.
</principle>

<principle name="portable_paths">
Never hardcode machine-specific absolute paths in commands, reports, or evidence.
Use `$SKILL_DIR` for skill-internal paths, `$REDHAT_WORKSPACE` for cross-repo paths,
and `$NAMESPACE` for cluster resources.
</principle>

<principle name="no_destructive_actions">
Never run cleanup, teardown, namespace deletion, or operator removal without explicit user confirmation. Preserve evidence before any cleanup. Read `references/recovery-and-rerun.md` before suggesting recovery steps.
</principle>

</essential_principles>

<intake>

## Orchestrator Release Validation

What would you like to do?

### Setup and Prerequisites

1. **Full release readiness check** — End-to-end validation of RHDH + Orchestrator + OSL
2. **Prerequisite check** — Verify tools, cluster access, and environment
3. **Normalize release target** — Parse and validate RHDH/OSL version + install mode

### Dependency and Risk Analysis

4. **Dependency delta analysis** — Compare versions across repos, flag drift
5. **OSL pre-release validation** — Validate env chain for an OSL RC/alpha/beta
6. **Cross-repo impact check** — Verify contract alignment across repos

### Evidence and Reporting

7. **Collect evidence bundle** — Gather diagnostics for triage or escalation
8. **Generate go/no-go report** — Produce structured decision report

### Troubleshooting

9. **Troubleshoot a failure** — Diagnose setup or runtime failures
10. **Recovery and rerun** — Clean up and retry after persistent failures

**Wait for response before proceeding.**

</intake>

<routing>

| Response | Script / Reference | Fallback |
|----------|-------------------|----------|
| 1, "full readiness", "end-to-end", "release readiness" | Run steps 2→3→4→(5 if pre-release)→6→7→8 in sequence | — |
| 2, "prereq", "prerequisites", "setup check" | `python "$SKILL_DIR/scripts/prereq_check.py" --json` | Manual checks below |
| 3, "target", "normalize", "version" | `python "$SKILL_DIR/scripts/release_target.py" <rhdh> <mode> [--osl <ver>] --json` | `references/release-matrix-selection.md` |
| 4, "dependency", "delta", "drift", "version mismatch" | `python "$SKILL_DIR/scripts/dependency_context.py" --json` | `references/dependency-delta-check.md` |
| 5, "OSL pre-release", "RC", "release candidate" | `references/osl-pre-release-path.md` | — |
| 6, "cross-repo", "contract", "impact" | `references/cross-repo-impact.md` | — |
| 7, "evidence", "diagnostics", "bundle" | `references/evidence-collection.md` | — |
| 8, "go/no-go", "report", "decision" | `python "$SKILL_DIR/scripts/go_no_go_report.py" --auto-decision -i <data> -f markdown` | — |
| 9, "troubleshoot", "debug", "failure", "broken" | `references/debugging-playbook.md` → classify via `references/failure-signatures.md` | — |
| 10, "recovery", "rerun", "cleanup", "retry" | `references/recovery-and-rerun.md` | — |

### Full Readiness Sequence (Response 1)

When the user asks for a complete release readiness check, execute these steps in order. Stop and report if any step produces a blocker.

1. **Prerequisites**: Run `prereq_check.py --json`. If `all_passed: false`, report blockers and stop.
2. **Target normalization**: Run `release_target.py` with user-provided versions. If `valid: false`, report errors and stop.
3. **Dependency delta**: Run `dependency_context.py --json`. Flag high-risk deltas as blockers.
4. **OSL pre-release** (if `is_pre_release_flow: true`): Walk through `osl-pre-release-path.md` validation checks.
5. **Cross-repo impact**: Walk through `cross-repo-impact.md` procedure. Flag contract mismatches as risks.
6. **Evidence collection**: Collect minimum evidence per `evidence-collection.md`.
7. **Go/no-go report**: Aggregate all blockers, risks, and evidence into `go_no_go_report.py`.

</routing>

<prerequisites>

**Run before any validation workflow:**

| Gate | Check | If fail |
|------|-------|---------|
| Tools on PATH | `python "$SKILL_DIR/scripts/prereq_check.py" --json` | Install missing tools; fix cluster login |
| Target tuple valid | `python "$SKILL_DIR/scripts/release_target.py" <args> --json` | Fix version format or install mode |
| Workspace repos accessible | `dependency_context.py` reports `unavailable_sources: 0` | Set `$RHDH_TEST_INSTANCE`, `$RHDH_OVERLAY_REPO` env vars |
| Cluster namespace exists | `oc get project "$NAMESPACE"` succeeds | Create namespace or fix `$NAMESPACE` |

Do not proceed past prerequisites if any gate fails. Report the failure and suggest fixes.

</prerequisites>

<success_criteria>

## What "Done" Looks Like

A release validation run is complete when:

- [ ] Target tuple is normalized and recorded
- [ ] All prerequisites pass
- [ ] Dependency context extracted with no unresolved high-risk deltas
- [ ] OSL pre-release env chain validated (if applicable)
- [ ] Cross-repo contracts checked — no unresolved mismatches
- [ ] Evidence bundle collected
- [ ] Go/no-go report generated with decision, blockers, risks, and next actions
- [ ] Decision is one of: `GO`, `GO_WITH_RISKS`, `NO_GO`

### Decision Rules

| Condition | Decision |
|-----------|----------|
| No blockers, no risks | `GO` |
| No blockers, risks present with mitigations | `GO_WITH_RISKS` |
| Any unresolved blocker | `NO_GO` |
| Untested critical path | `NO_GO` (absence of evidence for required checks) |

</success_criteria>

<reference_index>

| Reference | Purpose | Load when |
|-----------|---------|-----------|
| `references/release-matrix-selection.md` | Target tuple rules, install mode guidance, matrix expansion | Normalizing or selecting release targets |
| `references/dependency-delta-check.md` | Version mismatch detection workflow, risk classification | Running dependency analysis |
| `references/osl-pre-release-path.md` | Pre-release env chain, setup sequence, common failures | Target includes OSL RC/alpha/beta |
| `references/cross-repo-impact.md` | Repo dependency graph, contract surfaces, impact check | Verifying cross-repo alignment |
| `references/evidence-collection.md` | Diagnostics bundle contents, collection order, packaging | Collecting evidence for triage/report |
| `references/debugging-playbook.md` | Triage flow, setup/runtime failure diagnosis | Any failure during validation |
| `references/failure-signatures.md` | Symptom→cause mapping, classification rules | Classifying a specific failure |
| `references/recovery-and-rerun.md` | Cleanup levels, controlled rerun, stop conditions | Persistent failures needing retry |
| `../../rhdh/references/rhdh-repos.md` | Full repo map and ecosystem relationships | Cross-repo path resolution |
| `../../rhdh/references/versions.md` | RHDH/Backstage version compatibility matrix | Version compatibility questions |

</reference_index>
