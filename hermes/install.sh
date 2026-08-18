#!/usr/bin/env sh
set -eu

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HERMES_HOME=${HERMES_HOME:-"$HOME/.hermes"}
TARGET="$HERMES_HOME/skills/productivity/person-memory"

mkdir -p "$TARGET" "$HERMES_HOME/person-memory"
cp "$SRC_DIR/person-memory/SKILL.md" "$TARGET/SKILL.md"
mkdir -p "$TARGET/scripts"
cp "$SRC_DIR/person-memory/scripts/person_memory.py" "$TARGET/scripts/person_memory.py"
cp "$SRC_DIR/person-memory/scripts/trigger.py" "$TARGET/scripts/trigger.py"
cp "$SRC_DIR/person-memory/triggers.json" "$TARGET/triggers.json"
chmod +x "$TARGET/scripts/person_memory.py" "$TARGET/scripts/trigger.py"

python3 "$TARGET/scripts/person_memory.py" init >/dev/null

cat <<EOF
Installed person-memory skill at:
  $TARGET
Database:
  $HERMES_HOME/person-memory/memory.db

Optional dedicated-agent identity:
  cp "$SRC_DIR/hermes/SOUL.md" "$HERMES_HOME/SOUL.md"

Trigger examples:
  /person-memory 她说她不吃香菜
  python3 "$TARGET/scripts/trigger.py" --plain "她想去北海道"

Optional quick-command aliases are documented in:
  $SRC_DIR/hermes/config.example.yaml

Detailed trigger modes:
  $SRC_DIR/TRIGGERS.md

Router Agent rule example:
  $SRC_DIR/hermes/ROUTER_AGENTS.example.md

Then add the person, for example:
  python3 "$TARGET/scripts/person_memory.py" person-add "她" --relationship partner
EOF
