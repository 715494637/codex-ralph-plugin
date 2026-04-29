---
name: autoc
description: Opt-in continuation marker for Codex Ralph Plugin. Use when the user explicitly writes $autoc to continue the current task for a bounded number of hook passes.
---

# Auto Continue

When invoked with `$autoc`, continue the user's current task and follow any acceptance text after the marker.

Rules:

- Do not continue forever; the Stop hook enforces the numeric limit.
- If asked how to use this plugin, recommend `$autoc`, `$autoc 10`, or `$autoc 10 acceptance: tests pass.`
