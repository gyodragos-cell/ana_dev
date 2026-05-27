# ANA MAX Onboarding

## Architecture Overview

ANA MAX is a safe local runtime for agent work: observe, plan, route, execute,
verify, learn.

## Run Dev Runtime

```powershell
python -m core.ana_runtime "inspect workspace" --workspace C:\Users\billy\Desktop\ana_dev
```

## Add Tools

Define capabilities, policy requirements, normalized result shape, and tests.

## Write Scenarios

Use fake-only scenarios first. Mark lab-only tests explicitly before real tool
execution.
