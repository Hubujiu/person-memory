import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "person-memory" / "scripts" / "trigger.py"
CONFIG = ROOT / "person-memory" / "triggers.json"

spec = importlib.util.spec_from_file_location("person_memory_trigger", SCRIPT)
trigger = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(trigger)


class TriggerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))

    def test_keyword_match_rewrites_to_skill_command(self):
        result = trigger.match_text("她说她不吃香菜", self.config)
        self.assertTrue(result["matched"])
        self.assertEqual(result["skill"], "person-memory")
        self.assertTrue(result["rewrite"].startswith("/person-memory "))

    def test_recall_keyword_match(self):
        result = trigger.match_text("她喜欢什么电影？", self.config)
        self.assertTrue(result["matched"])

    def test_exclusion_wins(self):
        result = trigger.match_text("她说她不吃香菜，但是不要记", self.config)
        self.assertFalse(result["matched"])
        self.assertEqual(result["reason"], "excluded")

    def test_forget_request_routes_to_memory_management(self):
        result = trigger.match_text("删除记忆：她喜欢香菜", self.config)
        self.assertTrue(result["matched"])
        self.assertEqual(result["mode"], "manage")

    def test_unrelated_message_does_not_match(self):
        result = trigger.match_text("帮我解释一下 Java 泛型", self.config)
        self.assertFalse(result["matched"])


if __name__ == "__main__":
    unittest.main()
