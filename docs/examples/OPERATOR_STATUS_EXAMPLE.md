# Operator Status Example

## Purpose

Show the compact read-only command ANA uses before install/reload work.

## Command

```powershell
python ANA_MAX/dev_artifacts/scripts/ana_operator_status.py
```

## Expected Clean Shape

```text
ANA Operator Status: vsix=1.0.71 package=PASS(main=True,copy=True) mcp_ready=True tools=90 reload=PASS marker=True tool_surface=PASS(live=90,manifest=90,extra=0,missing=0) behavior=PASS(checks=9/9) identity=PASS(files=10,violations=0,missing=0) files=created=<n>,deleted=0,modified=<n> memory=archive_candidates=<n>,date_basis=utc,readiness=PASS,moves=<n> maps=code:PASS(<n>) graph:PASS(<nodes>n/<edges>e)
checkpoint=SESSION_CHECKPOINT_<timestamp>.md
rem_sleep=REM_SLEEP_REPORT_<timestamp>.md(<timestamp>)
reports=no_reload:no_reload_quality_gate_<timestamp>.json:PASS(pass=8) lab:lab_quality_gate_<timestamp>.json:PASS(pass=10) nucleus:nucleus_smoke_<timestamp>.json:PASS(pass=9,warn=0,fail=0) autonomy:autonomy_runner_<timestamp>.json:PASS(pass=18,warn=0,fail=0) trace:autonomy_runner_<timestamp>.json:PASS(steps=18,spans=18,aligned=True)
next_action=Continue with one scoped lab action.
review=batch=runtime command=python -m compileall -q <area> plan=dry_run batches=<n> commands=<n> verified=<n>/<n> all_pass=true fresh=true
review_run=review_batch_runner_<timestamp>.json:PASS(mode=run,category=runtime,commands=2,pass=2,fail=0,timeout=0,planned=0)
review_runs=runtime:PASS(2/2,fail=0,timeout=0,fresh=true),script:PASS(2/2,fail=0,timeout=0,fresh=true),test:PASS(1/1,fail=0,timeout=0,fresh=true),config:PASS(2/2,fail=0,timeout=0,fresh=true),extension:PASS(2/2,fail=0,timeout=0,fresh=true),doc:PASS(1/1,fail=0,timeout=0,fresh=true)
install=.\ANA_MAX\dev_artifacts\scripts\install_latest_lab_vsix.ps1 -Apply
verify=python ANA_MAX/dev_artifacts/scripts/ana_post_reload_verify.py --no-write
```

## What This Proves

- The operator sees the current packaged VSIX version and whether both local
  VSIX artifacts exist.
- MCP readiness and live reload marker are visible in one command.
- Live MCP tool surface is compared against the local permission manifest, so a
  stale MCP process can show `extra_live` or `missing_live` drift after tool
  registration changes.
- Active lab and extension identity drift is visible without running the full
  Lab Quality Gate.
- Selected live behavior freshness is visible, including the `agent_coach`
  monitor-noise filter and context generated-memory noise filter, so the
  operator can spot a healthy but stale MCP process.
- If only `live_behavior_stale` is present, the next action is a direct ANA MCP
  restart instead of a VSIX install/reload flow.
- When reload diagnostics and latest Autonomy are PASS, the next action becomes
  one scoped lab action instead of another Autonomy loop.
- The first Patch Advisor review batch and first focused verification command
  from the latest Autonomy report are visible.
- The latest Autonomy dry-run Review Batch Plan summary is visible beside the
  first command, so the operator sees how many batches and commands are ready
  before choosing a scoped run.
- The review line also shows coverage from the recent Review Batch Runner
  ledger, so already verified batches are not rerun blindly.
- The review coverage is freshness-aware: if an active file changes after the
  latest report for its category, the line shows `fresh=false stale=<category>`
  and that category is not counted as verified.
- The latest Review Batch Runner execution report is visible separately, so the
  operator can see which category was actually run and how many commands passed.
- The recent Review Batch Runner ledger is visible by category, so the operator
  can confirm whether all active review batches have recent PASS evidence.
- The latest checkpoint pointer is visible.
- The latest REM Sleep report pointer is visible.
- The latest high-signal report filenames and verdict summaries are visible,
  including trace span alignment.
- Aggregate file activity is visible as created/deleted/modified counts for the
  authorized workspace snapshot.
- Memory hygiene is visible as current archive candidates, UTC archive date
  basis, plus latest dry-run readiness. The default policy keeps the latest 20
  checkpoints and latest 20 REM reports. `STALE` means the saved dry-run plan
  is valid but no longer covers every current candidate because new
  checkpoint/REM files appeared. `delta=+1` means one additional candidate
  exists beyond the saved plan.
- Context map freshness is visible as `maps=code:... graph:...`. `STALE`
  means active code/docs/tests changed after the last Code Map or Graph Map
  refresh, so refresh both maps before relying on structural context.
- If the latest Autonomy report is newer than the latest saved Trace Report,
  Operator Status validates trace alignment directly from the Autonomy report
  without writing a new file.
- The next install/verify commands are explicit.

## Safety

Read-only. Does not install, reload, restart, archive, or mutate files.

## Share Class

`private-lab, sanitizable`: remove local report paths and private checkpoint
names before sharing.


















