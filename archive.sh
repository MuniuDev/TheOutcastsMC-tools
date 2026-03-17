#!/bin/bash
set -euo pipefail

if [ -f .env ]; then
  set -a
  source .env
  set +a
fi

# Constants
EXCLUDE_FILE="${SERVER_DIR}/backup_exclude_list.txt"
DATE_STR=$(date +"%Y_%m_%d_%H_%M")
NPROC=$(( $(nproc) / 2 ))

# Parse arguments
FULL=false
POSITIONAL=()
for arg in "$@"; do
  case "$arg" in
    --full) FULL=true ;;
    *) POSITIONAL+=("$arg") ;;
  esac
done
case "${POSITIONAL[0]:-}" in
  server) SRC_DIR=${SERVER_DIR}; PREFIX="server" ;;
  backup) SRC_DIR=${BACKUP_DIR}; PREFIX="backup" ;;
  *) echo "Usage: $0 [server|backup] [--full]" >&2; exit 1 ;;
esac

# Load exclusions file
EXCLUDE_LINES=()
if [ "$FULL" = false ] && [ -f "$EXCLUDE_FILE" ]; then
  echo "Loading exclusions file from: $EXCLUDE_FILE"
  while IFS= read -r line || [[ -n "$line" ]]; do
    [[ -z "$line" || "$line" == \#* ]] && continue
    EXCLUDE_LINES+=("$line")
  done < "$EXCLUDE_FILE"
fi

# Handle backup exclusions and calculate backup size
EXCLUDE_ARGS=()
for line in "${EXCLUDE_LINES[@]}"; do
  EXCLUDE_ARGS+=(--exclude="$line")
done


# Calculate proper size of the backup, by subtracting exclusions
echo "Calculating backup size"
BACKUP_SIZE=$(du -sb "${SRC_DIR}" | awk '{print $1}')
for line in "${EXCLUDE_LINES[@]}"; do
  pattern="${line#\*\*/}"
  while IFS= read -r -d '' match; do
    excluded=$(du -sb "$match" 2>/dev/null | awk '{print $1}')
    BACKUP_SIZE=$((BACKUP_SIZE - excluded))
  done < <(find "${SRC_DIR}" -path "*/$pattern" -print0 2>/dev/null)
done

# Get human readable backup size
DST_ARCHIVE=$ARCHIVES_DIR/$SERVER_NAME-$PREFIX-$DATE_STR.tar.gz
if (( BACKUP_SIZE >= 1073741824 )); then
  BACKUP_SIZE_READABLE="$(awk "BEGIN {printf \"%.2f GB\", $BACKUP_SIZE / 1073741824}")"
else
  BACKUP_SIZE_READABLE="$(awk "BEGIN {printf \"%.2f MB\", $BACKUP_SIZE / 1048576}")"
fi

# Archive
echo "Archiving $SRC_DIR -> $DST_ARCHIVE (${BACKUP_SIZE_READABLE}, ${NPROC} threads, ${#EXCLUDE_LINES[@]} exclusions)"
mkdir -p "$ARCHIVES_DIR"
tar --wildcards --wildcards-match-slash -cf - "${EXCLUDE_ARGS[@]}" -C "$(dirname "${SRC_DIR}")" "$(basename "${SRC_DIR}")" \
  | pv -s ${BACKUP_SIZE} -N "$(basename "$DST_ARCHIVE")" -pterb \
  | pigz -p ${NPROC} > "$DST_ARCHIVE"
