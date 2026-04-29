#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from pathlib import Path


DEFAULT_COUNT = 5
MAX_TAIL_BYTES = 1_000_000
DIRECTIVE_RE = re.compile(r"^\s*\$codex-ralph-plugin\b\s*(?:(\d{1,3})\b)?\s*(.*)$", re.I)


def payload():
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def tail(path):
    try:
        file = Path(path)
        size = file.stat().st_size
        with file.open("rb") as handle:
            if size > MAX_TAIL_BYTES:
                handle.seek(size - MAX_TAIL_BYTES)
                handle.readline()
            return handle.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def records(text):
    out = []
    for line in text.splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            out.append(item)
    return out


def user_text(record):
    data = record.get("payload")
    if not isinstance(data, dict):
        return ""

    if record.get("type") == "response_item" and data.get("role") == "user":
        content = data.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            return "\n".join(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and isinstance(part.get("text"), str)
            )

    if record.get("type") == "event_msg" and data.get("type") == "user_message":
        body = data.get("payload")
        if isinstance(body, dict):
            return str(body.get("message") or "")

    return ""


def directive(data):
    transcript = data.get("transcript_path")
    if not transcript:
        return None

    items = records(tail(transcript))
    turn_id = str(data.get("turn_id") or "")
    if turn_id:
        for index, item in enumerate(items):
            body = item.get("payload")
            if (
                item.get("type") == "turn_context"
                and isinstance(body, dict)
                and str(body.get("turn_id") or "") == turn_id
            ):
                items = items[index:]

    text = "\n".join(filter(None, (user_text(item) for item in items)))
    for line in reversed(text.splitlines()):
        match = DIRECTIVE_RE.match(line)
        if not match:
            continue
        count = max(1, int(match.group(1) or DEFAULT_COUNT))
        criteria = (match.group(2) or "").strip()
        if criteria.lower().startswith("acceptance:"):
            criteria = criteria[len("acceptance:") :].strip()
        return count, criteria
    return None


def state_file(data):
    root = os.environ.get("PLUGIN_DATA")
    root = Path(root) if root else Path(data.get("cwd") or ".") / ".codex-ralph-plugin"
    key = f"{data.get('session_id') or 'session'}:{data.get('turn_id') or 'turn'}"
    return root / f"{hashlib.sha256(key.encode()).hexdigest()[:32]}.json"


def count_at(path):
    try:
        return int(json.loads(path.read_text(encoding="utf-8")).get("count", 0))
    except Exception:
        return 0


def main():
    data = payload()
    parsed = directive(data)
    if not parsed:
        return 0

    max_count, criteria = parsed
    path = state_file(data)
    count = count_at(path)
    if count >= max_count:
        return 0

    count += 1
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"count": count}), encoding="utf-8")

    reason = (
        f"Codex Ralph Plugin pass {count}/{max_count}. "
        f"Continue the task. The number after the marker is the pass limit, not task content. "
        f"Acceptance: {criteria or 'finish the latest request'}."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
