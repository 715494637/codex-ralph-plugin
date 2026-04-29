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


def record(kind, payload):
    return {"type": kind, "payload": payload}


def user(text):
    return record("response_item", {"role": "user", "content": [{"text": text}]})


def transcript(records):
    handle = tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False)
    with handle:
        for item in records:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    return Path(handle.name)


class AutoContinueTests(unittest.TestCase):
    def test_parse_dollar_autoc(self):
        path = transcript([user("$autoc 10 acceptance: tests pass")])
        try:
            parsed = auto_continue.directive({"transcript_path": str(path)})
        finally:
            path.unlink(missing_ok=True)
        self.assertEqual(parsed, (10, "tests pass"))

    def test_hook_blocks_until_limit(self):
        with tempfile.TemporaryDirectory() as data_dir:
            path = transcript([user("$autoc 2 acceptance: tests pass")])
            payload = {
                "cwd": str(ROOT),
                "session_id": "session-1",
                "turn_id": "turn-1",
                "transcript_path": str(path),
            }
            env = {**os.environ, "PLUGIN_DATA": data_dir}
            try:
                runs = [
                    subprocess.run(
                        [sys.executable, str(HOOK_PATH)],
                        input=json.dumps(payload),
                        text=True,
                        capture_output=True,
                        env=env,
                        check=True,
                    )
                    for _ in range(3)
                ]
            finally:
                path.unlink(missing_ok=True)

        self.assertIn('"decision": "block"', runs[0].stdout)
        self.assertIn("pass 1/2", runs[0].stdout)
        self.assertIn("pass 2/2", runs[1].stdout)
        self.assertEqual("", runs[2].stdout.strip())


if __name__ == "__main__":
    unittest.main()
