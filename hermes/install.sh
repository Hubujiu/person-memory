#!/usr/bin/env sh
set -eu

SRC_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
HERMES_HOME=${HERMES_HOME:-"$HOME/.hermes"}
TARGET="$HERMES_HOME/skills/productivity/person-memory"

mkdir -p "$TARGET" "$HERMES_HOME/person-memory"
cp "$SRC_DIR/person-memory/SKILL.md" "$TARGET/SKILL.md"
mkdir -p "$TARGET/scripts"
cp "$SRC_DIR/person-memory/scripts/person_memory.py" "$TARGET/scripts/person_memory.py"
chmod +x "$TARGET/scripts/person_memory.py"

python3 "$TARGET/scripts/person_memory.py" init >/dev/null

cat <<EOF
Installed person-memory skill at:
  $TARGET
Database:
  $HERMES_HOME/person-memory/memory.db

Optional dedicated-agent identity:
  cp "$SRC_DIR/hermes/SOUL.md" "$HERMES_HOME/SOUL.md"

Then add the person, for example:
  python3 "$TARGET/scripts/person_memory.py" person-add "她" --relationship partner
EOF
