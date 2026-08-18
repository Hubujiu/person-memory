#!/usr/bin/env python3
import argparse
import json
import sqlite3
import sys
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

DEFAULT_DB = Path.home() / ".hermes" / "person-memory" / "memory.db"

SCHEMA = r'''
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS persons (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    aliases_json TEXT NOT NULL DEFAULT '[]',
    relationship TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    speaker TEXT NOT NULL DEFAULT 'person',
    content TEXT NOT NULL,
    source TEXT,
    source_ref TEXT,
    occurred_at TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_messages_person_time
ON messages(person_id, occurred_at DESC);

CREATE TABLE IF NOT EXISTS memories (
    id TEXT PRIMARY KEY,
    person_id TEXT NOT NULL REFERENCES persons(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    category TEXT NOT NULL,
    topic TEXT NOT NULL,
    value TEXT NOT NULL,
    sentiment TEXT,
    confidence REAL NOT NULL DEFAULT 1.0 CHECK(confidence >= 0 AND confidence <= 1),
    importance INTEGER NOT NULL DEFAULT 3 CHECK(importance BETWEEN 1 AND 5),
    status TEXT NOT NULL DEFAULT 'active',
    evidence_quote TEXT,
    source_message_id TEXT REFERENCES messages(id) ON DELETE SET NULL,
    valid_from TEXT,
    valid_to TEXT,
    metadata_json TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_memories_lookup
ON memories(person_id, category, topic, status, updated_at DESC);

CREATE INDEX IF NOT EXISTS idx_memories_kind
ON memories(person_id, kind, status);
'''


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def connect(db_path: Path) -> sqlite3.Connection:
    db_path = db_path.expanduser()
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA)
    try:
        conn.executescript(r'''
        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            message_id UNINDEXED,
            person_id UNINDEXED,
            content,
            tokenize='unicode61'
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts USING fts5(
            memory_id UNINDEXED,
            person_id UNINDEXED,
            category,
            topic,
            value,
            evidence_quote,
            tokenize='unicode61'
        );
        ''')
    except sqlite3.OperationalError:
        pass
    conn.commit()


def get_person(conn: sqlite3.Connection, name_or_id: str) -> sqlite3.Row | None:
    row = conn.execute("SELECT * FROM persons WHERE id=? OR lower(name)=lower(?)", (name_or_id, name_or_id)).fetchone()
    if row:
        return row
    for row in conn.execute("SELECT * FROM persons"):
        aliases = json.loads(row["aliases_json"] or "[]")
        if any(str(a).lower() == name_or_id.lower() for a in aliases):
            return row
    return None


def require_person(conn: sqlite3.Connection, name_or_id: str) -> sqlite3.Row:
    row = get_person(conn, name_or_id)
    if not row:
        raise SystemExit(f"Unknown person: {name_or_id}. Add them first.")
    return row


def cmd_person_add(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    existing = get_person(conn, args.name)
    if existing:
        print(json.dumps(dict(existing), ensure_ascii=False))
        return
    pid = args.id or str(uuid.uuid4())
    ts = now_iso()
    aliases = [x.strip() for x in (args.aliases or "").split(",") if x.strip()]
    conn.execute(
        "INSERT INTO persons(id,name,aliases_json,relationship,created_at,updated_at) VALUES(?,?,?,?,?,?)",
        (pid, args.name, json.dumps(aliases, ensure_ascii=False), args.relationship, ts, ts),
    )
    conn.commit()
    print(json.dumps({"id": pid, "name": args.name}, ensure_ascii=False))


def insert_message(conn: sqlite3.Connection, person_id: str, content: str, speaker: str = "person", source: str | None = None,
                   source_ref: str | None = None, occurred_at: str | None = None) -> str:
    mid = str(uuid.uuid4())
    ts = now_iso()
    conn.execute(
        "INSERT INTO messages(id,person_id,speaker,content,source,source_ref,occurred_at,created_at) VALUES(?,?,?,?,?,?,?,?)",
        (mid, person_id, speaker, content, source, source_ref, occurred_at, ts),
    )
    try:
        conn.execute("INSERT INTO messages_fts(message_id,person_id,content) VALUES(?,?,?)", (mid, person_id, content))
    except sqlite3.OperationalError:
        pass
    return mid


def cmd_message_add(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    person = require_person(conn, args.person)
    mid = insert_message(conn, person["id"], args.text, args.speaker, args.source, args.source_ref, args.occurred_at)
    conn.commit()
    print(json.dumps({"message_id": mid}, ensure_ascii=False))


def normalize_memory(m: dict[str, Any]) -> dict[str, Any]:
    required = ["kind", "category", "topic", "value"]
    missing = [k for k in required if not str(m.get(k, "")).strip()]
    if missing:
        raise ValueError(f"memory missing fields: {', '.join(missing)}")
    return {
        "kind": str(m["kind"]).strip(),
        "category": str(m["category"]).strip(),
        "topic": str(m["topic"]).strip(),
        "value": str(m["value"]).strip(),
        "sentiment": m.get("sentiment"),
        "confidence": max(0.0, min(1.0, float(m.get("confidence", 1.0)))),
        "importance": max(1, min(5, int(m.get("importance", 3)))),
        "status": str(m.get("status", "active")),
        "evidence_quote": m.get("evidence_quote"),
        "valid_from": m.get("valid_from"),
        "valid_to": m.get("valid_to"),
        "metadata": m.get("metadata") or {},
    }


def insert_memory(conn: sqlite3.Connection, person_id: str, m: dict[str, Any], source_message_id: str | None) -> str:
    m = normalize_memory(m)
    # Conservative dedupe: exact active fact from same category/topic/value updates confidence/time instead of duplicating.
    existing = conn.execute(
        """SELECT id FROM memories WHERE person_id=? AND category=? AND topic=? AND value=? AND status='active' ORDER BY updated_at DESC LIMIT 1""",
        (person_id, m["category"], m["topic"], m["value"]),
    ).fetchone()
    ts = now_iso()
    if existing:
        conn.execute(
            """UPDATE memories SET confidence=max(confidence,?), importance=max(importance,?), evidence_quote=COALESCE(?,evidence_quote),
               source_message_id=COALESCE(?,source_message_id), valid_from=COALESCE(?,valid_from), valid_to=COALESCE(?,valid_to),
               metadata_json=?, updated_at=? WHERE id=?""",
            (m["confidence"], m["importance"], m["evidence_quote"], source_message_id, m["valid_from"], m["valid_to"],
             json.dumps(m["metadata"], ensure_ascii=False), ts, existing["id"]),
        )
        return existing["id"]
    mem_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO memories(id,person_id,kind,category,topic,value,sentiment,confidence,importance,status,evidence_quote,
           source_message_id,valid_from,valid_to,metadata_json,created_at,updated_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (mem_id, person_id, m["kind"], m["category"], m["topic"], m["value"], m["sentiment"], m["confidence"],
         m["importance"], m["status"], m["evidence_quote"], source_message_id, m["valid_from"], m["valid_to"],
         json.dumps(m["metadata"], ensure_ascii=False), ts, ts),
    )
    try:
        conn.execute(
            "INSERT INTO memories_fts(memory_id,person_id,category,topic,value,evidence_quote) VALUES(?,?,?,?,?,?)",
            (mem_id, person_id, m["category"], m["topic"], m["value"], m["evidence_quote"] or ""),
        )
    except sqlite3.OperationalError:
        pass
    return mem_id


def cmd_remember_json(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    payload = json.load(sys.stdin) if args.input == "-" else json.loads(Path(args.input).read_text(encoding="utf-8"))
    person = require_person(conn, payload.get("person") or args.person)
    msg = payload.get("message") or {}
    message_id = None
    if msg.get("content"):
        message_id = insert_message(
            conn, person["id"], msg["content"], msg.get("speaker", "person"), msg.get("source"), msg.get("source_ref"), msg.get("occurred_at")
        )
    ids = []
    for m in payload.get("memories", []):
        ids.append(insert_memory(conn, person["id"], m, message_id))
    conn.commit()
    print(json.dumps({"person_id": person["id"], "message_id": message_id, "memory_ids": ids}, ensure_ascii=False))


def rows_json(rows):
    out = []
    for r in rows:
        d = dict(r)
        if "metadata_json" in d:
            try:
                d["metadata"] = json.loads(d.pop("metadata_json"))
            except Exception:
                pass
        out.append(d)
    return out


def cmd_recall(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    person = require_person(conn, args.person)
    q = args.query.strip()
    rows = []
    if q:
        try:
            rows = conn.execute(
                """SELECT m.* FROM memories_fts f JOIN memories m ON m.id=f.memory_id
                   WHERE f.person_id=? AND memories_fts MATCH ? AND m.status='active'
                   ORDER BY m.importance DESC, m.confidence DESC, m.updated_at DESC LIMIT ?""",
                (person["id"], q, args.limit),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f"%{q}%"
            rows = conn.execute(
                """SELECT * FROM memories WHERE person_id=? AND status='active' AND
                   (category LIKE ? OR topic LIKE ? OR value LIKE ? OR evidence_quote LIKE ?)
                   ORDER BY importance DESC, confidence DESC, updated_at DESC LIMIT ?""",
                (person["id"], like, like, like, like, args.limit),
            ).fetchall()
    else:
        clauses = ["person_id=?", "status='active'"]
        vals: list[Any] = [person["id"]]
        if args.category:
            clauses.append("category=?"); vals.append(args.category)
        if args.kind:
            clauses.append("kind=?"); vals.append(args.kind)
        vals.append(args.limit)
        rows = conn.execute(
            f"SELECT * FROM memories WHERE {' AND '.join(clauses)} ORDER BY importance DESC, confidence DESC, updated_at DESC LIMIT ?",
            vals,
        ).fetchall()
    print(json.dumps(rows_json(rows), ensure_ascii=False, indent=2))


def cmd_search_messages(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    person = require_person(conn, args.person)
    try:
        rows = conn.execute(
            """SELECT m.* FROM messages_fts f JOIN messages m ON m.id=f.message_id
               WHERE f.person_id=? AND messages_fts MATCH ? ORDER BY COALESCE(m.occurred_at,m.created_at) DESC LIMIT ?""",
            (person["id"], args.query, args.limit),
        ).fetchall()
    except sqlite3.OperationalError:
        rows = conn.execute(
            """SELECT * FROM messages WHERE person_id=? AND content LIKE ? ORDER BY COALESCE(occurred_at,created_at) DESC LIMIT ?""",
            (person["id"], f"%{args.query}%", args.limit),
        ).fetchall()
    print(json.dumps(rows_json(rows), ensure_ascii=False, indent=2))


def parse_iso_day(s: str) -> date | None:
    try:
        return date.fromisoformat(s[:10])
    except Exception:
        return None


def daily_alerts(conn: sqlite3.Connection, today: date, days_ahead: int) -> list[dict[str, Any]]:
    alerts: list[dict[str, Any]] = []
    persons = {r["id"]: r["name"] for r in conn.execute("SELECT id,name FROM persons")}
    rows = conn.execute("SELECT * FROM memories WHERE status='active'").fetchall()
    horizon = today + timedelta(days=days_ahead)
    for r in rows:
        meta = json.loads(r["metadata_json"] or "{}")
        # Important date / anniversary. Metadata: date=YYYY-MM-DD, recurring=annual, remind_days_before=N.
        if r["kind"] in {"important_date", "anniversary", "birthday", "holiday"} or r["category"] in {"dates", "important_dates"}:
            ds = str(meta.get("date") or r["value"])
            d = parse_iso_day(ds)
            if d:
                recurring = meta.get("recurring") == "annual"
                candidate = d
                if recurring:
                    try:
                        candidate = date(today.year, d.month, d.day)
                    except ValueError:
                        candidate = date(today.year, 2, 28)
                    if candidate < today:
                        try:
                            candidate = date(today.year + 1, d.month, d.day)
                        except ValueError:
                            candidate = date(today.year + 1, 2, 28)
                lead = int(meta.get("remind_days_before", 7))
                if today <= candidate <= horizon or 0 <= (candidate - today).days <= lead:
                    alerts.append({
                        "type": "important_date",
                        "person": persons.get(r["person_id"]),
                        "topic": r["topic"],
                        "date": candidate.isoformat(),
                        "days_until": (candidate - today).days,
                        "note": r["value"],
                    })
        # Menstrual cycle estimate. Explicitly approximate, not medical advice.
        if r["kind"] == "menstrual_cycle" or (r["category"] == "health" and r["topic"] == "menstrual_cycle"):
            last = parse_iso_day(str(meta.get("last_start_date") or r["value"]))
            avg = int(meta.get("average_cycle_days", 28))
            lead = int(meta.get("notify_lead_days", 3))
            if last and 15 <= avg <= 60:
                candidate = last
                while candidate < today:
                    candidate += timedelta(days=avg)
                delta = (candidate - today).days
                if 0 <= delta <= max(days_ahead, lead):
                    alerts.append({
                        "type": "cycle_estimate",
                        "person": persons.get(r["person_id"]),
                        "estimated_start": candidate.isoformat(),
                        "days_until": delta,
                        "average_cycle_days": avg,
                        "note": "Calendar estimate only; cycles can vary.",
                    })
    return sorted(alerts, key=lambda x: x.get("days_until", 9999))


def cmd_daily_check(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    today = date.fromisoformat(args.today) if args.today else date.today()
    alerts = daily_alerts(conn, today, args.days_ahead)
    if args.json:
        print(json.dumps(alerts, ensure_ascii=False, indent=2))
        return
    if not alerts:
        return
    for a in alerts:
        if a["type"] == "important_date":
            print(f"[重要日期] {a['person']} · {a['topic']}：{a['date']}（还有 {a['days_until']} 天）")
        else:
            print(f"[经期预估] {a['person']}：预计 {a['estimated_start']} 左右开始（还有 {a['days_until']} 天；仅按历史周期估算）")


def cmd_profile(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    person = require_person(conn, args.person)
    rows = conn.execute(
        """SELECT category,topic,value,sentiment,confidence,importance,evidence_quote,updated_at
           FROM memories WHERE person_id=? AND status='active'
           ORDER BY category, importance DESC, confidence DESC, updated_at DESC""",
        (person["id"],),
    ).fetchall()
    grouped: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        grouped.setdefault(r["category"], []).append(dict(r))
    print(json.dumps({"person": person["name"], "profile": grouped}, ensure_ascii=False, indent=2))


def cmd_stats(conn: sqlite3.Connection, args: argparse.Namespace) -> None:
    person = require_person(conn, args.person)
    result = {
        "person": person["name"],
        "messages": conn.execute("SELECT count(*) FROM messages WHERE person_id=?", (person["id"],)).fetchone()[0],
        "memories": conn.execute("SELECT count(*) FROM memories WHERE person_id=? AND status='active'", (person["id"],)).fetchone()[0],
        "categories": {r[0]: r[1] for r in conn.execute("SELECT category,count(*) FROM memories WHERE person_id=? AND status='active' GROUP BY category", (person["id"],))},
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Lightweight person-memory store for Hermes Agent")
    p.add_argument("--db", default=str(DEFAULT_DB), help="SQLite database path")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init")

    s = sub.add_parser("person-add")
    s.add_argument("name"); s.add_argument("--id"); s.add_argument("--aliases"); s.add_argument("--relationship")

    s = sub.add_parser("message-add")
    s.add_argument("--person", required=True); s.add_argument("--text", required=True); s.add_argument("--speaker", default="person")
    s.add_argument("--source"); s.add_argument("--source-ref"); s.add_argument("--occurred-at")

    s = sub.add_parser("remember-json")
    s.add_argument("--person"); s.add_argument("--input", default="-", help="JSON file or - for stdin")

    s = sub.add_parser("recall")
    s.add_argument("--person", required=True); s.add_argument("--query", default=""); s.add_argument("--category"); s.add_argument("--kind"); s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("search-messages")
    s.add_argument("--person", required=True); s.add_argument("--query", required=True); s.add_argument("--limit", type=int, default=20)

    s = sub.add_parser("profile")
    s.add_argument("--person", required=True)

    s = sub.add_parser("daily-check")
    s.add_argument("--today"); s.add_argument("--days-ahead", type=int, default=7); s.add_argument("--json", action="store_true")

    s = sub.add_parser("stats")
    s.add_argument("--person", required=True)
    return p


def main() -> None:
    p = build_parser(); args = p.parse_args()
    conn = connect(Path(args.db)); init_db(conn)
    if args.cmd == "init":
        print(str(Path(args.db).expanduser())); return
    dispatch = {
        "person-add": cmd_person_add,
        "message-add": cmd_message_add,
        "remember-json": cmd_remember_json,
        "recall": cmd_recall,
        "search-messages": cmd_search_messages,
        "profile": cmd_profile,
        "daily-check": cmd_daily_check,
        "stats": cmd_stats,
    }
    dispatch[args.cmd](conn, args)

if __name__ == "__main__":
    main()
