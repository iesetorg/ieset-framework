# Preflight-Ready Inconclusive Review - 2026-05-03

## Decision

Do not bulk-rerun the existing inconclusive pool yet.

The audit found `57` currently preflight-ready inconclusive runs, but `56` of those run directories already have uncommitted changes. Rerunning them now would overwrite work from the broader dirty worktree. The only clean run directory is `hong_kong_no_industrial_policy_frontier_comparison`, but that spec is still `candidate`, not `pre_registered`, so it should not be converted into scoreboard-facing evidence without an explicit pre-run promotion/audit step.

## Counts

- Preflight-ready inconclusive candidates: `57`
- Dirty run directories skipped: `56`
- Clean run directories: `1`
- Clean pre-registered run directories: `0`

## Clean Candidate Held Back

- `hong_kong_no_industrial_policy_frontier_comparison` | template=`panel_fe` | status=`candidate` | reason held back: not pre-registered

## Methodology Guard

- Do not overwrite dirty `engine/runs/<id>` artifacts without first deciding whether those uncommitted changes belong to another active wave.
- Do not score candidate/draft hypotheses as school-scoreboard evidence.
- If the Hong Kong candidate should be run, first promote it with an audit that states it had only a prior inconclusive preflight artifact and has not yet received an estimable verdict.
