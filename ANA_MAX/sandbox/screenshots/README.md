# ANA MAX Screenshot Sandbox

Put raw visual QA screenshots here only.

This folder is private mother-lab workspace material and must not be synced
directly to the public release.

## Rules

- Capture only ANA MAX, the extension cockpit, public Marketplace/GitHub/site
  pages, or safe demo windows.
- Avoid private chats, tokens, emails, local user data, API keys, unrelated
  desktop windows, and private file paths.
- If a screenshot includes local paths or personal content, mark it
  `not-public-safe` in the QA report.
- Do not crop, blur, or publish from here without a review pass.

## Recommended Names

```text
01-activity-bar-runtime.png
02-cockpit-smart-ready.png
03-session-wake.png
04-rest-preview.png
05-marketplace-page.png
06-github-readme.png
07-github-pages-home.png
```

## Inventory

After captures are created, run from the workspace root:

```powershell
python ANA_MAX\dev_artifacts\scripts\screenshot_asset_inventory.py
```

It writes `asset_inventory.json` in this folder. That JSON is ignored by git and
is only for review.

Use `docs/VISUAL_ASSET_INTAKE_TEMPLATE.md` to decide which images are safe
enough for public README, site, or Marketplace use.
