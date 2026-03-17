#!/bin/bash
set -euo pipefail

# Constants
NPROC=$(( $(nproc) / 2 ))

ARCHIVE="${1:-}"
if [ -z "$ARCHIVE" ]; then
  echo "Usage: $0 <archive.tar.gz>" >&2
  exit 1
fi

ARCHIVE_SIZE=$(stat -c %s "$ARCHIVE")
pigz -dc -p $NPROC "$ARCHIVE" \
  | pv -s "$ARCHIVE_SIZE" -N "$(basename "$ARCHIVE")" -pterb \
  | tar -x -C "$(dirname "$ARCHIVE")"
