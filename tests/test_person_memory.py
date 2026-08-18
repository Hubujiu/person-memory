import importlib.util
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path

SCRIPT = Path(__file__).parents[1] / "person-memory" / "scripts" / "person_memory.py"
spec = importlib.util.spec_from_file_location("pm", SCRIPT)
pm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pm)

class PersonMemoryTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "memory.db"
        self.conn = pm.connect(self.db)
        pm.init_db(self.conn)
        ts = pm.now_iso()
        self.conn.execute("INSERT INTO persons(id,name,aliases_json,created_at,updated_at) VALUES(?,?,?,?,?)", ("p1", "她", "[]", ts, ts))
        self.conn.commit()

    def tearDown(self):
        self.conn.close(); self.tmp.cleanup()

    def test_message_and_memory(self):
        mid = pm.insert_message(self.conn, "p1", "我一直很喜欢寿司")
        mem = {
            "kind": "preference", "category": "food", "topic": "like", "value": "寿司",
            "confidence": 1.0, "importance": 4, "evidence_quote": "我一直很喜欢寿司"
        }
        pm.insert_memory(self.conn, "p1", mem, mid)
        self.conn.commit()
        self.assertEqual(self.conn.execute("select count(*) from messages").fetchone()[0], 1)
        self.assertEqual(self.conn.execute("select count(*) from memories").fetchone()[0], 1)

    def test_dedupe_exact_memory(self):
        mem = {"kind":"preference","category":"food","topic":"like","value":"寿司"}
        pm.insert_memory(self.conn, "p1", mem, None)
        pm.insert_memory(self.conn, "p1", mem, None)
        self.conn.commit()
        self.assertEqual(self.conn.execute("select count(*) from memories").fetchone()[0], 1)

    def test_annual_date_alert(self):
        m = {
            "kind":"anniversary", "category":"important_dates", "topic":"纪念日", "value":"2025-05-20",
            "metadata":{"date":"2025-05-20","recurring":"annual","remind_days_before":7}
        }
        pm.insert_memory(self.conn, "p1", m, None); self.conn.commit()
        alerts = pm.daily_alerts(self.conn, date(2026,5,18), 7)
        self.assertEqual(alerts[0]["days_until"], 2)

    def test_cycle_estimate(self):
        m = {
            "kind":"menstrual_cycle", "category":"health", "topic":"menstrual_cycle", "value":"2026-08-02",
            "metadata":{"last_start_date":"2026-08-02","average_cycle_days":29,"notify_lead_days":3}
        }
        pm.insert_memory(self.conn, "p1", m, None); self.conn.commit()
        alerts = pm.daily_alerts(self.conn, date(2026,8,29), 7)
        self.assertEqual(alerts[0]["estimated_start"], "2026-08-31")

if __name__ == "__main__":
    unittest.main()
