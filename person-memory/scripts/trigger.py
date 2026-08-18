#!/usr/bin/env python3
"""Deterministic keyword/regex trigger helper for person-memory.

This is intentionally independent from Hermes internals. A gateway, Weixin
adapter, or router can call it before invoking Hermes.

Exit codes:
  0: matched person-memory
  1: no match
  2: invalid input/config
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "triggers.json"


def load_config(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"cannot read trigger config {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("trigger config must be a JSON object")
    return data


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def match_text(text: str, config: dict) -> dict:
    normalized = normalize(text)
    lowered = normalized.casefold()

    for phrase in config.get("exclude", []):
        if str(phrase).casefold() in lowered:
            return {
                "matched": False,
                "skill": config.get("skill", "person-memory"),
                "reason": "excluded",
                "matched_terms": [phrase],
            }

    matched_terms: list[str] = []
    matched_groups: list[str] = []
    keyword_groups = config.get("keywords", {})
    for group, keywords in keyword_groups.items():
        group_hits = [kw for kw in keywords if str(kw).casefold() in lowered]
        if group_hits:
            matched_terms.extend(group_hits)
            matched_groups.append(group)

    # Management/update intent must win over generic content phrases. Recall
    # should also win over ordinary remember phrases when both appear.
    priority = config.get("group_priority", ["manage", "recall", "remember"])
    matched_group = next((group for group in priority if group in matched_groups), None)
    if matched_group is None and matched_groups:
        matched_group = matched_groups[0]

    regex_hits: list[str] = []
    for pattern in config.get("regex", []):
        if re.search(pattern, normalized, flags=re.IGNORECASE):
            regex_hits.append(pattern)

    matched = bool(matched_terms or regex_hits)
    skill = config.get("skill", "person-memory")
    result = {
        "matched": matched,
        "skill": skill,
        "mode": matched_group or ("regex" if regex_hits else None),
        "matched_terms": matched_terms,
        "matched_regex": regex_hits,
    }
    if matched:
        result["rewrite"] = f"/{skill} {normalized}".strip()
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Match a message against person-memory triggers")
    parser.add_argument("text", nargs="?", help="message text; reads stdin when omitted")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="path to triggers.json")
    parser.add_argument("--plain", action="store_true", help="print only rewritten command on match")
    args = parser.parse_args()

    text = args.text if args.text is not None else sys.stdin.read()
    if not text.strip():
        print(json.dumps({"matched": False, "reason": "empty"}, ensure_ascii=False))
        return 1

    try:
        config = load_config(Path(args.config).expanduser())
        result = match_text(text, config)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.plain:
        if result["matched"]:
            print(result["rewrite"])
    else:
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result["matched"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
