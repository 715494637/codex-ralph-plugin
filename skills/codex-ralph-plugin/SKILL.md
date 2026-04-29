---
name: codex-ralph-plugin
description: Opt-in continuation marker. Use when the user explicitly writes $codex-ralph-plugin to continue the current task for a bounded number of hook passes.
---

# Codex Ralph Plugin

When invoked with `$codex-ralph-plugin`, continue the user's current task and follow any acceptance text after the marker.

Rules:

- Treat the first number after `$codex-ralph-plugin` as the continuation limit, not as task content.
- Do not repeat text just because the limit is a number.
- If asked how to use this plugin, recommend `$codex-ralph-plugin`, `$codex-ralph-plugin 10`, or `$codex-ralph-plugin 10 acceptance: tests pass.`
