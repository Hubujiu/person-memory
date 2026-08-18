# Router Agent — Person Memory routing rule

Add a rule like this to the Router Agent's `AGENTS.md` (Hermes' documented project/agent instruction filename). Adapt the destination profile/agent name to your deployment.

## Route: person-memory

Route the message to the `person-memory` agent/skill when the user's intent is to **store, update, search, recall, or use facts about a specific important person**.

Strong routing signals include:

- forwarded/quoted messages from that person;
- “记住/记一下/帮我记” followed by something about that person;
- likes/dislikes, food or dietary restrictions, drinks, restaurants;
- travel wishes, places they want to visit, activities they want to try;
- movies, anime, games, books, music, idols, brands, clothing or gifts;
- habits, recurring behaviors, explicit personality traits or communication style;
- birthday, anniversary, meaningful dates, deliberately supplied menstrual-cycle calendar data;
- recall questions such as “她之前说过什么？” “她喜欢吃什么？” “她想去哪里？” “她提过想要什么礼物？”

Do **not** route ordinary relationship advice merely because the message mentions a partner. Route only when person-memory storage/retrieval would materially help.

When routing, preserve the user's original text verbatim. Do not summarize away quoted evidence before the memory agent sees it.

Suggested route payload:

```json
{
  "route": "person-memory",
  "reason": "store_or_recall_person_fact",
  "message": "<original user message verbatim>"
}
```

If your router can invoke a Hermes profile directly, forward the original message with the `person-memory` skill preloaded. If it can only emit text, rewrite to:

```text
/person-memory <original user message>
```

For deterministic routing before the LLM, call:

```bash
python3 ~/.hermes/skills/productivity/person-memory/scripts/trigger.py --plain "<message>"
```

Exit code `0` means route to person-memory; exit code `1` means leave the message to normal router logic.
