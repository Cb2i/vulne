#!/usr/bin/env bash
# Backs up the VulnAssist SQLite database to a timestamped file.
# (If you have migrated to PostgreSQL, use pg_dump instead — this script only
# covers the default SQLite setup.)
#
# Usage: ./scripts/backup.sh [destination-dir]

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_PATH="$ROOT_DIR/data/vulnassist.db"
DESTINATION="${1:-$ROOT_DIR/data/backups}"

if [ ! -f "$DB_PATH" ]; then
  echo "No SQLite database found at $DB_PATH. Nothing to back up (or you are using PostgreSQL)." >&2
  exit 1
fi

mkdir -p "$DESTINATION"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
BACKUP_FILE="$DESTINATION/vulnassist_${TIMESTAMP}.db"

cp "$DB_PATH" "$BACKUP_FILE"
echo "Backup created: $BACKUP_FILE"
