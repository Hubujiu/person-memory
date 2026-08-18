#!/usr/bin/env sh
set -eu

HERMES_HOME=${HERMES_HOME:-"$HOME/.hermes"}
SCRIPT="$HERMES_HOME/skills/productivity/person-memory/scripts/person_memory.py"
DELIVER=${1:-local}

if ! command -v hermes >/dev/null 2>&1; then
  echo "hermes CLI not found" >&2
  exit 1
fi

# Current Hermes supports script-only cron. If flags change in a future release,
# ask Hermes in natural language to create the same job.
hermes cron create "0 9 * * *" \
  --name "Person memory daily check" \
  --script "python3 $SCRIPT daily-check --days-ahead 7" \
  --no-agent \
  --deliver "$DELIVER"
