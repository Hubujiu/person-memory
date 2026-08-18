# Person Memory

A lightweight, local-first memory skill for **Hermes Agent** that remembers one person's preferences, wishes, habits, personality evidence, speaking style, meaningful experiences, important dates, and other small details without stuffing an entire profile into every prompt.

The core design is simple:

```text
forwarded message
      │
      ├── raw message ───────────────► SQLite `messages`
      │
      └── conservative extraction ───► SQLite `memories`
                                          │
                         targeted recall ◄┘
```

## Why

Long prose profiles are easy to write but expensive to inject into every model call, difficult to update, and hard to trace back to the original conversation. Person Memory stores compact structured facts in SQLite while keeping the original message as evidence.

It is designed for questions such as:

- What does she like to eat? What does she avoid?
- Which movies, anime, games, musicians or idols has she mentioned?
- Where has she said she wants to travel?
- What gifts has she casually said she likes?
- What recurring personality or communication patterns have actual evidence?
- What did she originally say, and when?
- Is an anniversary or other important date approaching?
- If cycle information was deliberately provided, is the next **approximate** calendar estimate approaching?

## Features

- Local SQLite database; no server or database service.
- Raw-message archive + structured long-term memories.
- Conservative distinction between stable preferences and temporary states.
- Evidence quotes and confidence per memory.
- Categories for food, travel, films, anime, games, music, idols, gifts, personality, speech style, habits, dates, and more.
- SQLite FTS5 search when available, with `LIKE` fallback.
- WAL mode for reliable lightweight operation (`memory.db`, plus temporary `-wal`/`-shm` files while active).
- Hermes-compatible `SKILL.md` with progressive disclosure.
- Script-only daily Hermes cron check: reminders without daily LLM token spend.
- Standard-library Python only. No pip dependencies.

## Repository Layout

```text
person-memory/
├── README.md
├── LICENSE
├── .gitignore
├── person-memory/
│   ├── SKILL.md
│   └── scripts/
│       └── person_memory.py
├── hermes/
│   ├── SOUL.md
│   ├── config.example.yaml
│   ├── install.sh
│   └── setup-cron.sh
└── tests/
    └── test_person_memory.py
```

## Install for Hermes

```bash
git clone <repo-url>
cd person-memory
./hermes/install.sh
```

Then register the person you want to remember:

```bash
python3 ~/.hermes/skills/productivity/person-memory/scripts/person_memory.py \
  person-add "她" --aliases "宝贝,女朋友" --relationship partner
```

The dedicated `SOUL.md` is optional. If this Hermes profile exists only for this purpose:

```bash
cp hermes/SOUL.md ~/.hermes/SOUL.md
```

Do **not** overwrite an existing multi-purpose profile's `SOUL.md` unless that is intended.

## Example: remember a forwarded message

Hermes reads the message, loads the skill, performs conservative extraction, and writes both the raw message and structured memory. The low-level operation looks like this:

```bash
cat <<'JSON' | python3 ~/.hermes/skills/productivity/person-memory/scripts/person_memory.py remember-json
{
  "person": "她",
  "message": {
    "speaker": "person",
    "content": "我一直特别想去北海道，冬天去看雪。",
    "source": "wechat"
  },
  "memories": [
    {
      "kind": "wish",
      "category": "travel",
      "topic": "destination",
      "value": "北海道",
      "confidence": 1.0,
      "importance": 4,
      "evidence_quote": "我一直特别想去北海道，冬天去看雪。",
      "metadata": {"preferred_season": "冬天", "reason": "看雪"}
    }
  ]
}
JSON
```

## Recall

```bash
PM=~/.hermes/skills/productivity/person-memory/scripts/person_memory.py

python3 "$PM" recall --person "她" --category food
python3 "$PM" recall --person "她" --kind wish
python3 "$PM" recall --person "她" --query "北海道"
python3 "$PM" search-messages --person "她" --query "北海道"
python3 "$PM" profile --person "她"
```

## Memory semantics

Person Memory deliberately avoids turning every sentence into a permanent personality trait.

| Statement | Stored as |
|---|---|
| “今天突然想吃火锅” | temporary state |
| “我一直都很喜欢火锅” | stable preference |
| “我不吃香菜” | explicit dislike |
| “有机会想去冰岛” | travel wish |
| “我就是比较慢热” | explicit personality evidence |
| one short reply | **not** evidence that the person is introverted |

Every meaningful structured memory can keep an `evidence_quote`, `confidence`, source message, and timestamps.

## Important dates and daily checks

Important dates are stored as normal structured memories with date metadata. Run:

```bash
python3 ~/.hermes/skills/productivity/person-memory/scripts/person_memory.py daily-check --days-ahead 7
```

No output means there is nothing to remind you about.

Hermes supports scheduled jobs and script-only cron execution, so this deterministic check does not need an LLM. On a current Hermes installation:

```bash
./hermes/setup-cron.sh local
```

Or ask Hermes in natural language to create a daily 09:00 script-only job that runs the command above and delivers non-empty output to your preferred gateway.

## Cycle estimates

Cycle tracking is optional sensitive data. Person Memory only uses dates deliberately supplied by the user/person. It does not infer cycle information from mood, behavior, purchases, or other messages.

The daily checker can estimate the next start date from a provided last start date and average cycle length. This is only a calendar estimate; real cycles vary and this feature is not a medical prediction.

## Privacy

This project is local-first. The actual database is intentionally ignored by Git. If you sync or back it up, treat it as highly private data: it can contain another person's conversations, preferences, health-related dates, and relationship history.

Use it with the other person's privacy and consent in mind. Do not expose the database to unrelated agents by default.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## License

MIT
