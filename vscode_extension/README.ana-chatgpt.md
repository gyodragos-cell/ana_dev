ANA MAX ChatGPT Hybrid Extension
================================

This is a lightweight hybrid VS Code extension manifest and README that
enables connecting a ChatGPT-based channel to the local ANA MAX runtime.

Purpose
-------
- Keep existing Codex support while adding a separate `ana.chatgpt.connect`
  command that routes chat messages from this channel into the `ana-max-bridge`.

Usage
-----
1. Install the base extension (ANA MAX Codex cockpit) as usual.
2. Register the hybrid manifest by packaging a VSIX that uses
   `package.ana-chat-gpt.json` as the manifest (or copy entries into the
   main `package.json` if you prefer).
3. The hybrid command `ANA MAX: Connect ChatGPT Channel` will appear in the
   command palette and can be wired to your ChatGPT integration.

Notes
-----
- This file is intentionally minimal; the extension shares `extension.js`
  implementation with the main cockpit to avoid duplicating logic.
