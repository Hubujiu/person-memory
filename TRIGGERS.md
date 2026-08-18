# Person Memory Trigger Modes

Person Memory supports four trigger patterns. The first three are directly usable with this repository. The fourth is a routing convention for multi-agent deployments.

## 1. Native Hermes semantic trigger

Hermes can select an installed skill from natural conversation. Person Memory already describes its intended cases in `person-memory/SKILL.md`, especially the `description` and `When to Use` sections.

Examples:

```text
她说她不吃香菜，帮我记住。
记一下，她以后想去北海道看雪。
她之前提过喜欢什么电影？
她有没有说过想要什么礼物？
```

No wrapper process is needed. Hermes sees the installed skill index and can load `person-memory` with `skill_view` when the request matches.

This mode is semantic rather than deterministic: the model decides whether the skill is relevant. It is the best default for a dedicated Person Memory Agent because the user can simply forward messages or ask questions naturally.

### Recommended SKILL.md trigger wording

Keep the skill description concrete and include common intents such as:

```text
Remember and recall a specific person's preferences, dislikes, wishes, habits,
personality evidence, speaking style, important dates and forwarded messages.
Use when the user asks to remember something about that person, forwards what
she/he said, or asks what she/he likes, avoids, wants, said, watches, plays,
follows, or where they want to go.
```

The `When to Use` section should explicitly mention forwarded/quoted messages, likes/dislikes, travel wishes, gifts, media preferences, habits, personality evidence, speech style, important dates and recall questions.

## 2. Deterministic keyword / regex trigger

Hermes currently documents semantic skill selection and slash-command skill loading, but not an arbitrary plain-message keyword hook that runs before the LLM. For a Weixin adapter, gateway preprocessor, or Router that must make a deterministic decision first, this repository ships a tiny standard-library helper:

```bash
python3 ~/.hermes/skills/productivity/person-memory/scripts/trigger.py \
  '她说她不吃香菜'
```

Example matched output:

```json
{
  "matched": true,
  "skill": "person-memory",
  "mode": "remember",
  "matched_terms": ["她说", "她不吃"],
  "matched_regex": [],
  "rewrite": "/person-memory 她说她不吃香菜"
}
```

For adapter integration, use `--plain`:

```bash
python3 ~/.hermes/skills/productivity/person-memory/scripts/trigger.py \
  --plain '她想去冰岛看极光'
```

Output:

```text
/person-memory 她想去冰岛看极光
```

Exit codes:

- `0`: matched; route/rewrite to Person Memory.
- `1`: no match; continue normal routing.
- `2`: invalid trigger configuration or input.

The keyword configuration is stored in:

```text
~/.hermes/skills/productivity/person-memory/triggers.json
```

The default config has four concepts:

- `keywords.remember`: phrases such as `记住`, `帮我记`, `记一下`, `她说`, `她喜欢`, `她想去`, `忌口`, `纪念日`, `经期`.
- `keywords.recall`: phrases such as `她喜欢什么`, `她想去哪里`, `她之前说过`, `还记得她`.
- `regex`: broader patterns such as `她 ... 喜欢/不喜欢/想去/想要`.
- `exclude`: explicit negative instructions such as `不要记`, `别记`, `不用记`, `忘掉`, `删除记忆`.

Exclusions take priority over positive matches.

### Adapter integration

Minimal Python pattern:

```python
import subprocess

result = subprocess.run(
    ["python3", trigger_path, "--plain", incoming_text],
    capture_output=True,
    text=True,
)

if result.returncode == 0:
    send_to_hermes(result.stdout.strip())
else:
    send_to_normal_router(incoming_text)
```

For a Weixin adapter:

```text
Weixin message
     │
     ▼
trigger.py
     │
     ├── exit 0 ──► rewrite `/person-memory <original>` ──► Memory Agent
     │
     └── exit 1 ──► normal Router Agent
```

The trigger script decides only **which skill should receive the message**. It must not decide that a sentence is a permanent preference/personality trait. The Person Memory skill still performs conservative extraction and stores evidence.

## 3. Slash-command trigger

Hermes automatically exposes installed skills as dynamic slash commands. After installation:

```text
/person-memory 她说她不吃香菜，记住这个。
/person-memory 她想去哪里旅行？
/person-memory 她之前有没有提过喜欢什么游戏？
```

Any text after the skill command is attached to the loaded skill as the task.

### Short aliases

Hermes Quick Commands can alias a shorter command to `/person-memory`. Merge this into `~/.hermes/config.yaml`:

```yaml
quick_commands:
  pm:
    type: alias
    target: /person-memory
  remember:
    type: alias
    target: /person-memory
  person:
    type: alias
    target: /person-memory
```

Then:

```text
/pm 她说她不吃香菜
/remember 她说她很喜欢《情书》
/person 她想去哪里？
```

Hermes forwards the user's trailing arguments to the alias target, so these become `/person-memory ...` without custom command code.

Use the full `/person-memory` command as the stable interface. Treat `/pm`, `/remember`, etc. as user-configurable conveniences.

## 4. Router Agent dispatch

For a multi-agent architecture, keep the final routing policy in the Router Agent rather than hard-coding one transport into this skill. A ready-made rule is in:

```text
hermes/ROUTER_AGENTS.example.md
```

Hermes uses `AGENTS.md` for project/agent instructions, so copy or adapt that rule into the Router Agent's `AGENTS.md`.

The router should send a message to Person Memory when the intent is to **store, update, search, recall, or use facts about a specific important person**.

Strong signals include forwarded/quoted messages, food preferences or restrictions, travel wishes, media/game/idol preferences, gifts, habits, explicit personality traits, speaking style, birthdays, anniversaries, meaningful dates and deliberately supplied cycle-calendar data.

Do not route generic relationship advice merely because the message mentions a partner.

Preserve the original forwarded/quoted text verbatim. Do not summarize away evidence before Person Memory receives it.

A router may emit a structured payload:

```json
{
  "route": "person-memory",
  "reason": "store_or_recall_person_fact",
  "message": "<original user message verbatim>"
}
```

Or, if the router communicates with Hermes by text, simply emit:

```text
/person-memory <original user message>
```

For deterministic pre-routing, the Router Agent's adapter can run `trigger.py` first and only use model-based routing when it does not match.