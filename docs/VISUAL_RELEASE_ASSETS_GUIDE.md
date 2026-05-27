# Visual Release Assets Guide

Last updated: 2026-05-27

Purpose: turn raw ANA MAX screenshots into public-safe release assets for
GitHub, the public site, and the Marketplace.

## Source Folder

Raw screenshots from agents or manual capture go here:

```text
ANA_MAX/sandbox/screenshots/
```

This is a private mother-lab folder. Do not sync it directly to the clean public
release.

After capture, create a local inventory:

```powershell
python ANA_MAX\dev_artifacts\scripts\screenshot_asset_inventory.py
```

Then use `docs/VISUAL_ASSET_INTAKE_TEMPLATE.md` for the review decision.

## Required Public-Safe Checks

Before any screenshot is copied to README, docs, site, or Marketplace assets,
check:

- No tokens, API keys, passwords, secrets, emails, or private account details.
- No private chat content or personal browser tabs.
- No unrelated desktop windows.
- No local paths unless the path is intentionally generic or cropped out.
- No confusing old version labels such as `1.0.9` for the v1.0.12 release.
- No stale tool count without context. Mother lab is 86 tools; clean public
  release is 85 tools.
- No popups that make calm read-only flows look unsafe.

## Target Screenshot Set

Use 3-5 strong images, not a large gallery:

| Asset | Purpose | Best Location |
| --- | --- | --- |
| Activity Bar Runtime | Proves visible beginner controls. | README, Marketplace |
| Cockpit Smart Ready | Shows runtime health and agent readiness. | README, Site |
| Wake Session | Shows context continuity. | Site |
| Rest Preview | Shows safe REM preview before saving. | README |
| Marketplace Page | Proof of install surface. | Site/news section |

## Recommended Captions

```text
ANA MAX cockpit keeps the local MCP runtime visible and beginner-friendly.
Smart Ready verifies the router, coach, memory, and lifecycle tools before work starts.
Wake Session resumes from the last REM handoff so agents do not start blind.
Rest Preview analyzes the session without writing memory until the user chooses Save REM.
```

## Decision Rules

- If an image is clean and useful, copy an edited public-safe version into the
  public release asset folder during a planned sync.
- If it is useful but contains private content, crop or blur it before public
  use.
- If it is visually noisy or version-stale, keep it in sandbox only.
- If the screenshot exposes private information, delete or quarantine it from
  public workflows.
