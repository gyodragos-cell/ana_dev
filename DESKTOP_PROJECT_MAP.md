# Desktop Project Map

This file is the quick control map for Billy.

## Main Folders

### C:\Users\billy\Desktop\ana_dev

Purpose:

- active development workspace
- experiments
- demos
- ANA tool testing
- voice testing
- Codex repair work

Git:

- local git repo
- no remote configured right now
- dirty workspace with many modified, deleted, and untracked files

Rule:

- do not publish directly from here
- do not let Qoder edit here
- use Codex/Cursor/Windsurf/Antigravity only with diff review

### C:\Users\billy\Desktop\ANA_MAX_GitHub_Release

Purpose:

- clean public release repo
- website `index.html`
- public README/docs
- GitHub remote

Git remote:

```text
https://github.com/gyodragos-cell/ANA-MAX-v0.1.0-beta---Advanced-Neural-Architecture.git
```

Public site target:

```text
https://gyodragos-cell.github.io/ANA-MAX-v0.1.0-beta---Advanced-Neural-Architecture/
```

Rule:

- keep public-safe
- no local paths
- no private logs, memories, screenshots, keys, db files
- only push after checking diff

## Agent Rules

Use for code/release work:

- Codex
- Cursor
- Windsurf
- Antigravity

Use Qoder only for:

- voice companion
- read-only Google/web reading
- demo narration
- brainstorming

Do not let Qoder:

- auto-fix repo files
- rewrite docs
- delete files
- change dependencies
- push to GitHub

## Current Known State

`ana_dev`:

- many changes from experiments and repairs
- needs careful triage before commit or cleanup

`ANA_MAX_GitHub_Release`:

- connected to GitHub
- current local changes: website button fixes, Runtime WorkGraph interaction,
  README site link, GitHub Pages workflow, publish guide

## Safe Workflow

1. Choose the folder first.
2. Run `git status --short --branch`.
3. Read before editing.
4. Make one small change.
5. Check `git diff`.
6. Run the smallest relevant test.
7. Commit only when the diff is understood.

