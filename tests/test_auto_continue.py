import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HOOK_PATH = ROOT / "hooks" / "auto_continue.py"

spec = importlib.util.spec_from_file_location("auto_continue", HOOK_PATH)
auto_continue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auto_continue)


def turn(turn_id):
    return {"type": "turn_context", "payload": {"turn_id": turn_id}}


def message(role, text):
    content_type = "input_text" if role == "user" else "output_text"
    return {
        "type": "response_item",
        "payload": {
            "role": role,
            "content": [{"type": content_type, "text": text}],
        },
    }


def write_rollout(records):
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
    with handle:
        for record in records:
            line = {"timestamp": "2026-04-29T00:00:00Z", **record}
            handle.write(json.dumps(line, ensure_ascii=False) + "\n")
    return Path(handle.name)


def transcript_context(records, turn_id="t1"):
    path = write_rollout(records)
    try:
        return auto_continue.transcript_context(
            {
                "transcript_path": str(path),
                "turn_id": turn_id,
                "last_assistant_message": None,
            }
        )
    finally:
        path.unlink(missing_ok=True)


class AutoContinueTests(unittest.TestCase):
    def test_default_is_disabled(self):
        context = transcript_context(
            [turn("t1"), message("user", "finish task"), message("assistant", "I will continue")]
        )
        self.assertFalse(context["directive"]["enabled"])
        self.assertFalse(auto_continue.should_continue(context, 0))

    def test_autoc_enables_default_limit(self):
        context = transcript_context(
            [
                turn("t1"),
                message("user", "/autoc acceptance: tests pass\nfinish task"),
                message("assistant", "I will continue"),
            ]
        )
        self.assertTrue(context["directive"]["enabled"])
        self.assertEqual(context["directive"]["max_count"], 5)
        self.assertEqual(context["directive"]["criteria"], "tests pass\nfinish task")
        self.assertTrue(auto_continue.should_continue(context, 0))

    def test_leading_space_autoc_enables_directive(self):
        context = transcript_context(
            [
                turn("t1"),
                message("user", " /autoc 1 acceptance: tests pass\nfinish task"),
                message("assistant", "I will continue"),
            ]
        )
        self.assertTrue(context["directive"]["enabled"])
        self.assertEqual(context["directive"]["max_count"], 1)
        self.assertEqual(context["directive"]["criteria"], "tests pass\nfinish task")
        self.assertTrue(auto_continue.should_continue(context, 0))

    def test_custom_limit_is_enforced(self):
        context = transcript_context(
            [
                turn("t1"),
                message("user", "/autoc 10 acceptance: build passes"),
                message("assistant", "I will continue"),
            ]
        )
        self.assertEqual(context["directive"]["max_count"], 10)
        self.assertTrue(auto_continue.should_continue(context, 9))
        self.assertFalse(auto_continue.should_continue(context, 10))

    def test_longer_command_does_not_enable(self):
        context = transcript_context(
            [
                turn("t1"),
                message("user", "/autocx 10 acceptance: build passes"),
                message("assistant", "I will continue"),
            ]
        )
        self.assertFalse(context["directive"]["enabled"])
        self.assertFalse(auto_continue.should_continue(context, 0))

    def test_done_marker_stops(self):
        context = transcript_context(
            [
                turn("t1"),
                message("user", "/autoc 3 criteria: done"),
                message("assistant", "Done <!-- AUTO_CONTINUE_DONE -->"),
            ]
        )
        self.assertFalse(auto_continue.should_continue(context, 0))

    def test_hook_script_blocks_until_limit(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            transcript = write_rollout(
                [
                    turn("t1"),
                    message("user", "/autoc 2 acceptance: tests pass"),
                    message("assistant", "I will continue"),
                ]
            )
            payload = {
                "cwd": str(ROOT),
                "hook_event_name": "Stop",
                "last_assistant_message": "I will continue",
                "model": "test-model",
                "permission_mode": "default",
                "session_id": "session-1",
                "stop_hook_active": False,
                "transcript_path": str(transcript),
                "turn_id": "t1",
            }
            env = os.environ.copy()
            env["PLUGIN_DATA"] = temp_dir
            try:
                first = subprocess.run(
                    [sys.executable, str(HOOK_PATH)],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    env=env,
                    check=True,
                )
                second = subprocess.run(
                    [sys.executable, str(HOOK_PATH)],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    env=env,
                    check=True,
                )
                third = subprocess.run(
                    [sys.executable, str(HOOK_PATH)],
                    input=json.dumps(payload),
                    text=True,
                    capture_output=True,
                    env=env,
                    check=True,
                )
            finally:
                transcript.unlink(missing_ok=True)

        self.assertIn('"decision": "block"', first.stdout)
        self.assertIn("Codex Ralph Plugin pass 1/2", first.stdout)
        self.assertIn("Codex Ralph Plugin pass 2/2", second.stdout)
        self.assertEqual(third.stdout.strip(), "")


if __name__ == "__main__":
    unittest.main()
