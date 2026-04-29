---
name: autoc
description: Opt-in continuation marker for Codex Ralph Plugin. Use when the user explicitly writes $autoc to ask Codex to continue an unfinished task for a bounded number of passes until the stated acceptance criteria are met.
---

# Auto Continue

When invoked with `$autoc`, treat it as an explicit request to finish the user's current task, verify the result when possible, and stop when the task is complete.

Rules:

- Do not continue forever; the Stop hook enforces the numeric limit.
- Respect the user's acceptance criteria after `$autoc`.
- When the task is complete, provide the final concise answer and do not do extra work.
- If asked how to use this plugin, recommend `$autoc`, `$autoc 10`, or `$autoc 10 acceptance: tests pass and final answer summarizes the change.`
