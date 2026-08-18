---
name: person-memory
description: Remember a person's life, preferences, and important dates.
version: 0.1.0
author: Hubujiu
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [memory, relationships, sqlite, personal-assistant]
    category: productivity
    requires_toolsets: [terminal]
    config:
      - key: person_memory.db_path
        description: SQLite database used by person-memory.
        default: ~/.hermes/person-memory/memory.db
        prompt: Person-memory database path
---

# Person Memory

## Overview

Use this skill as a durable memory for a specific person. The goal is not to invent a personality; it is to preserve what the person actually said or what the user explicitly observed, then turn useful details into compact structured memories.

The SQLite database is the source of truth. Store the raw forwarded message and the extracted facts. Never replace evidence with a summary alone.

Script path relative to this skill:

```bash
python3 scripts/person_memory.py
```

Default database:

```text
~/.hermes/person-memory/memory.db
```

SQLite WAL mode may additionally create `memory.db-wal` and `memory.db-shm` while the database is active.

## When to Use

Use this skill when the user:

- forwards or quotes something a loved one or important person said;
- says “remember this about her/him/them”;
- asks what the person likes, dislikes, avoids, wants, watches, plays, follows, or dreams about;
- asks about the person's personality, habits, communication style, recurring preferences, or meaningful experiences;
- asks what gift, restaurant, trip, movie, anime, game, idol, activity, or date might matter based on previously stored evidence;
- asks whether an important date or an approximate menstrual-cycle reminder is approaching.

Do not use this skill to fabricate traits from weak evidence. Do not silently convert a temporary state into a stable preference.

## First-Time Setup

1. Initialize the database:

```bash
python3 scripts/person_memory.py init
```

2. Add the person once:

```bash
python3 scripts/person_memory.py person-add "她" --aliases "宝贝,女朋友" --relationship partner
```

Use the user's chosen name/alias. Never guess a legal name.

## Memory Model

Every incoming message can produce two layers:

1. `messages`: the original text, source, speaker, and time. This is evidence and should be preserved when the user forwards or quotes the message.
2. `memories`: compact structured facts extracted from that message.

Allowed `kind` values are open-ended, but prefer these:

- `preference` — stable like/dislike/preference;
- `wish` — wants to do/go/buy/experience;
- `temporary_state` — wants or feels something right now;
- `fact` — explicit factual information;
- `personality_trait` — repeated or explicit personality characteristic;
- `speech_style` — stable communication or phrasing tendency;
- `habit` — repeated behavior or routine;
- `experience` — meaningful past event;
- `important_date` / `anniversary` / `birthday` / `holiday` — dates worth remembering;
- `menstrual_cycle` — calendar-only cycle tracking supplied by the user/person.

Recommended categories:

`food`, `drink`, `travel`, `movie`, `anime`, `game`, `music`, `idol`, `book`, `fashion`, `gift`, `activity`, `place`, `personality`, `speech`, `habit`, `family`, `friends`, `work`, `study`, `dream`, `fear`, `important_dates`, `health`, `other`.

## Ingesting a Forwarded Message

When the user forwards a message, first identify which stored person it belongs to. If the alias already resolves, do not ask again.

Extract memories conservatively. Then send one JSON document through stdin:

```bash
cat <<'JSON' | python3 scripts/person_memory.py remember-json
{
  "person": "她",
  "message": {
    "speaker": "person",
    "content": "我一直特别想去北海道，冬天去看雪。",
    "source": "wechat",
    "occurred_at": "2026-08-18T20:00:00+08:00"
  },
  "memories": [
    {
      "kind": "wish",
      "category": "travel",
      "topic": "destination",
      "value": "北海道",
      "sentiment": "like",
      "confidence": 1.0,
      "importance": 4,
      "evidence_quote": "我一直特别想去北海道，冬天去看雪。",
      "metadata": {
        "preferred_season": "冬天",
        "reason": "看雪"
      }
    }
  ]
}
JSON
```

One message may produce zero, one, or many memories. Always preserve the raw message even if nothing deserves structured extraction.

## Extraction Rules

### Stable preference vs temporary state

“今天突然想吃火锅” → `temporary_state`, not stable preference.

“我一直都特别喜欢吃火锅” → `preference`.

### Explicit evidence beats inference

If the person says “我不吃香菜”, store a food dislike with confidence near 1.0.

If the user merely says “她好像不太爱吃香菜”, store lower confidence and preserve that wording in `evidence_quote`.

### Personality requires stronger evidence

Do not infer `introverted`, `jealous`, `anxious`, `kind`, etc. from one ordinary message. Store a personality trait only when:

- the person explicitly describes themselves; or
- the user explicitly describes the trait; or
- the same pattern is repeatedly observed across messages.

For inferred repeated patterns, use confidence below 1.0 and keep evidence.

### Speech style

Store concrete tendencies, not imitations detached from evidence. Examples:

- frequently uses a specific catchphrase;
- prefers short replies;
- uses many sentence-final particles;
- avoids direct refusals;
- uses a nickname for the user.

Keep representative quotes in `evidence_quote`.

### Contradictions and change over time

People change. Do not delete old evidence simply because a new statement differs. Prefer a new active memory with `valid_from`, and mark old information inactive only when the new statement clearly supersedes it.

## Recall

Search compact memories first:

```bash
python3 scripts/person_memory.py recall --person "她" --query "北海道"
python3 scripts/person_memory.py recall --person "她" --category food
python3 scripts/person_memory.py recall --person "她" --kind wish
```

Search original messages when the user asks “她什么时候说过？” or wants exact context:

```bash
python3 scripts/person_memory.py search-messages --person "她" --query "北海道"
```

Get the entire compact profile:

```bash
python3 scripts/person_memory.py profile --person "她"
```

When answering, distinguish stored fact from inference. If evidence is available, mention the original wording or date only when useful; do not dump database internals.

## Important Dates

Store recurring dates with explicit metadata. Example:

```json
{
  "kind": "anniversary",
  "category": "important_dates",
  "topic": "在一起纪念日",
  "value": "2025-05-20",
  "confidence": 1.0,
  "importance": 5,
  "metadata": {
    "date": "2025-05-20",
    "recurring": "annual",
    "remind_days_before": 7
  }
}
```

Daily check:

```bash
python3 scripts/person_memory.py daily-check --days-ahead 7
```

No output means nothing is currently due.

## Menstrual-Cycle Reminder

Only store cycle information when the user deliberately provides it for this person. Treat it as sensitive health-related data. Do not infer cycle dates from mood, behavior, purchases, or unrelated messages.

Example memory metadata:

```json
{
  "kind": "menstrual_cycle",
  "category": "health",
  "topic": "menstrual_cycle",
  "value": "2026-08-02",
  "confidence": 1.0,
  "importance": 5,
  "metadata": {
    "last_start_date": "2026-08-02",
    "average_cycle_days": 29,
    "notify_lead_days": 3
  }
}
```

The daily checker performs only a simple calendar estimate from the supplied average cycle length. It must be phrased as an estimate, never as a medical conclusion or guarantee.

## Cron Recipe for Hermes

Hermes cron jobs can bind this skill. Prefer script-only cron for the daily check because it uses zero model tokens when the script itself produces the final reminder.

Example interactive setup:

```bash
hermes cron create "0 9 * * *" \
  --name "Person memory daily check" \
  --script 'python3 ~/.hermes/skills/productivity/person-memory/scripts/person_memory.py daily-check --days-ahead 7' \
  --no-agent \
  --deliver local
```

Replace `--deliver local` with the user's configured messaging destination when desired.

If the installed Hermes version uses a different CLI flag spelling, ask Hermes itself to create the same job in natural language; the underlying requirement is: daily at 09:00, script-only, run `daily-check`, deliver only non-empty output.

## Privacy Rules

- Keep the database local by default.
- Never commit `memory.db`, `memory.db-wal`, or `memory.db-shm` to Git.
- Do not expose sensitive memories to unrelated agents unless the user explicitly configures that sharing.
- Health, sexual, financial, authentication, and precise-location information should not be inferred.
- Forget/update requests must be honored by modifying the stored record rather than merely hiding it in chat.

## Common Pitfalls

1. **Over-personalizing from one message.** Use `temporary_state` or lower confidence.
2. **Keeping only summaries.** Preserve original messages so memories are auditable.
3. **Keeping only raw chat.** Extract compact memories so recall stays fast and token-efficient.
4. **Treating old preferences as eternal.** Preserve time and allow later updates.
5. **Sending the whole profile into every prompt.** Query only relevant categories/topics.
6. **Using an LLM for deterministic reminders.** Prefer script-only cron for date/cycle checks.

## Verification Checklist

- [ ] `python3 scripts/person_memory.py init` succeeds.
- [ ] The target person is present in `persons`.
- [ ] A forwarded message is preserved in `messages`.
- [ ] Structured memories include evidence and confidence.
- [ ] `recall` returns only relevant compact rows.
- [ ] `search-messages` can recover original wording.
- [ ] `daily-check` emits reminders only when due.
- [ ] Database files are excluded from Git.
