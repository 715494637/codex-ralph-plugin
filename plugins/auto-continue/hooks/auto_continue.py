#!/usr/bin/env python3
import hashlib
import json
import os
import re
import sys
from pathlib import Path


DONE_MARKER = "AUTO_CONTINUE_DONE"
DEFAULT_MAX_COUNT = 5
MAX_TRANSCRIPT_BYTES = 2_000_000

INCOMPLETE_PATTERNS = [
    r"\b(i will|i'll|next i|now i|going to|need to|todo|pending|remaining|continue|continuing)\b",
    r"\u6211\u4f1a|\u63a5\u4e0b\u6765|\u4e0b\u4e00\u6b65|\u8fd8\u9700\u8981|\u7ee7\u7eed|\u672a\u5b8c\u6210|\u51c6\u5907",
]

DONE_PATTERNS = [
    r"\b(done|completed|implemented|fixed|resolved|verified)\b",
    r"\btests?\s+(passed|passing)\b",
    r"\u5df2\u5b8c\u6210|\u5b8c\u6210\u4e86|\u5df2\u4fee\u590d|\u4fee\u590d\u4e86|\u6d4b\u8bd5\u901a\u8fc7|\u9a8c\u8bc1\u901a\u8fc7",
]

TOOL_HINT_PATTERNS = [
    r'"type"\s*:\s*"(function_call|custom_tool_call|local_shell_call|mcp_tool_call)"',
    r'"type"\s*:\s*"(exec_command|file_change|patch_apply)',
    r"\b(apply_patch|shell_command|exec_command|local_shell)\b",
]

COMMAND_PATTERN = re.compile(r"^\s*/autoc\b(?P<rest>.*)$", re.IGNORECASE)
COUNT_PATTERN = re.compile(
    r"^\s*(?:-{0,2}(?:max|count|times|loops)|\u6b21\u6570|\u5faa\u73af)?\s*[=:\uff1a]?\s*(?P<count>\d{1,3})\b",
    re.IGNORECASE,
)
CRITERIA_PATTERN = re.compile(
    r"(?:\u9a8c\u6536(?:\u6807\u51c6)?|\u6807\u51c6|acceptance(?:\s+criteria)?|criteria|until|done\s+when)\s*[=:\uff1a]\s*(?P<criteria>.+)",
    re.IGNORECASE | re.DOTALL,
)


def read_payload() -> dict:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        return {}
    return value if isinstance(value, dict) else {}


def read_text_tail(path: Path, max_bytes: int = MAX_TRANSCRIPT_BYTES) -> str:
    try:
        size = path.stat().st_size
        with path.open("rb") as handle:
            if size > max_bytes:
                handle.seek(size - max_bytes)
                handle.readline()
            return handle.read().decode("utf-8", errors="replace")
    except Exception:
        return ""


def parse_json_records(text: str) -> list[dict]:
    stripped = text.strip()
    if not stripped:
        return []

    try:
        value = json.loads(stripped)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            return [value]
    except json.JSONDecodeError:
        pass

    records = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            records.append(value)
    return records


def compact_json(value: object) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    except Exception:
        return ""


def value_at(value: object, *keys: str) -> object:
    current = value
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def record_turn_id(record: dict) -> str | None:
    payload = record.get("payload")
    if record.get("type") == "turn_context" and isinstance(payload, dict):
        turn_id = payload.get("turn_id")
        return str(turn_id) if turn_id else None

    event_payload = value_at(record, "payload", "payload")
    if isinstance(event_payload, dict):
        for key in ("turn_id", "id"):
            turn_id = event_payload.get(key)
            if turn_id:
                return str(turn_id)
    return None


def select_turn_records(records: list[dict], turn_id: str) -> list[dict]:
    if not records or not turn_id:
        return records

    start = None
    for index, record in enumerate(records):
        if record.get("type") == "turn_context" and record_turn_id(record) == turn_id:
            start = index

    if start is None:
        for index, record in enumerate(records):
            if record_turn_id(record) == turn_id:
                start = index
                break

    if start is None:
        return records[-80:]
    return records[start:]


def content_text(content: object) -> str:
    chunks = []
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict):
                text = item.get("text")
                if isinstance(text, str):
                    chunks.append(text)
            elif isinstance(item, str):
                chunks.append(item)
    elif isinstance(content, str):
        chunks.append(content)
    return "\n".join(chunk for chunk in chunks if chunk)


def response_item_text(record: dict) -> tuple[str | None, str]:
    if record.get("type") != "response_item":
        return None, ""
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None, ""

    role = payload.get("role")
    if isinstance(role, str):
        return role, content_text(payload.get("content"))

    item_type = payload.get("type")
    if item_type in {"function_call", "custom_tool_call", "local_shell_call"}:
        return "tool", compact_json(payload)
    if item_type in {"function_call_output", "custom_tool_call_output"}:
        return "tool_output", compact_json(payload)
    return None, ""


def event_text(record: dict) -> tuple[str | None, str]:
    if record.get("type") != "event_msg":
        return None, ""
    payload = record.get("payload")
    if not isinstance(payload, dict):
        return None, ""
    event_type = payload.get("type")
    event_payload = payload.get("payload")
    if not isinstance(event_payload, dict):
        return None, ""
    if event_type == "agent_message":
        return "assistant", str(event_payload.get("message") or "")
    if event_type == "user_message":
        message = event_payload.get("message")
        if isinstance(message, str):
            return "user", message
        return "user", compact_json(event_payload.get("input") or event_payload)
    return None, ""


def is_auto_continue_prompt(text: str) -> bool:
    lowered = text.lower()
    return (
        "auto-continue pass" in lowered
        or "<hook_prompt" in lowered
        or "hook_run_id=" in lowered
    )


def matches_any(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def parse_autoc_directive(user_text: str) -> dict:
    lines = user_text.splitlines()
    for index in range(len(lines) - 1, -1, -1):
        match = COMMAND_PATTERN.match(lines[index])
        if not match:
            continue

        rest = match.group("rest").strip()
        count = DEFAULT_MAX_COUNT
        count_match = COUNT_PATTERN.search(rest)
        if count_match:
            count = max(1, int(count_match.group("count")))

        tail = "\n".join([rest, *lines[index + 1 : index + 8]]).strip()
        criteria = ""
        criteria_match = CRITERIA_PATTERN.search(tail)
        if criteria_match:
            criteria = criteria_match.group("criteria").strip()
        elif rest:
            criteria = COUNT_PATTERN.sub("", rest, count=1).strip(" -:=\uff1a")

        return {
            "enabled": True,
            "max_count": count,
            "criteria": criteria,
        }

    return {
        "enabled": False,
        "max_count": DEFAULT_MAX_COUNT,
        "criteria": "",
    }


def transcript_context(payload: dict) -> dict:
    transcript_path = payload.get("transcript_path")
    if not transcript_path:
        user_text = ""
        return {
            "available": False,
            "assistant_text": str(payload.get("last_assistant_message") or ""),
            "user_text": user_text,
            "raw": "",
            "tool_seen": False,
            "directive": parse_autoc_directive(user_text),
        }

    raw = read_text_tail(Path(str(transcript_path)))
    records = parse_json_records(raw)
    turn_records = select_turn_records(records, str(payload.get("turn_id") or ""))
    assistant_messages = []
    user_messages = []
    scoped_raw = "\n".join(compact_json(record) for record in turn_records)

    for record in turn_records:
        role, text = response_item_text(record)
        if role is None:
            role, text = event_text(record)
        if not text or is_auto_continue_prompt(text):
            continue
        if role == "assistant":
            assistant_messages.append(text)
        elif role == "user":
            user_messages.append(text)

    fallback_message = str(payload.get("last_assistant_message") or "")
    if fallback_message and (not assistant_messages or assistant_messages[-1] != fallback_message):
        assistant_messages.append(fallback_message)

    user_text = "\n\n".join(user_messages[-3:])
    return {
        "available": bool(records),
        "assistant_text": "\n\n".join(assistant_messages[-6:]),
        "user_text": user_text,
        "raw": scoped_raw,
        "tool_seen": matches_any(TOOL_HINT_PATTERNS, scoped_raw),
        "directive": parse_autoc_directive(user_text),
    }


def state_file(payload: dict) -> Path:
    data_root = os.environ.get("PLUGIN_DATA") or os.environ.get("CLAUDE_PLUGIN_DATA")
    if data_root:
        root = Path(data_root)
    else:
        root = Path(payload.get("cwd") or ".") / ".codex-auto-continue"
    session_id = str(payload.get("session_id") or "unknown-session")
    turn_id = str(payload.get("turn_id") or "unknown-turn")
    digest = hashlib.sha256(f"{session_id}:{turn_id}".encode("utf-8")).hexdigest()[:32]
    return root / "state" / f"{digest}.json"


def load_count(path: Path) -> int:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return int(value.get("count", 0))
    except Exception:
        return 0


def save_count(path: Path, count: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"count": count}), encoding="utf-8")


def should_continue(context: dict, count: int) -> bool:
    directive = context.get("directive") or {}
    if not directive.get("enabled"):
        return False

    max_count = int(directive.get("max_count") or DEFAULT_MAX_COUNT)
    if max_count <= 0 or count >= max_count:
        return False

    assistant_text = context.get("assistant_text", "")

    # Only trust the marker when the assistant produced it. Hook prompts also
    # contain this marker instruction and are persisted as user messages.
    if DONE_MARKER in assistant_text:
        return False
    if directive.get("criteria"):
        return True
    if matches_any(INCOMPLETE_PATTERNS, assistant_text):
        return True
    if matches_any(DONE_PATTERNS, assistant_text) and not matches_any(
        INCOMPLETE_PATTERNS, assistant_text
    ):
        return False
    if context.get("tool_seen"):
        return True

    return os.environ.get("AUTO_CONTINUE_AGGRESSIVE", "1") != "0"


def main() -> int:
    payload = read_payload()
    context = transcript_context(payload)
    directive = context.get("directive") or {}
    max_count = int(directive.get("max_count") or DEFAULT_MAX_COUNT)
    criteria = str(directive.get("criteria") or "").strip()
    path = state_file(payload)
    count = load_count(path)

    if not should_continue(context, count):
        return 0

    next_count = count + 1
    save_count(path, next_count)
    criteria_text = criteria or "the user's latest requested work is complete"
    reason = (
        f"Auto-continue pass {next_count}/{max_count}. The user explicitly enabled this turn "
        "with /autoc. Review the full visible conversation history and continue only "
        "while work remains unfinished. Acceptance criteria: "
        f"{criteria_text}. If the criteria are satisfied, stop doing extra work, provide the "
        "final concise answer, and append "
        f"<!-- {DONE_MARKER} --> at the very end."
    )
    print(json.dumps({"decision": "block", "reason": reason}, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
