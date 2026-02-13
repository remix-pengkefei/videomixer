#!/bin/bash
#
# Validates all downloaded .mp4 files using ffprobe.
# Removes any corrupt/invalid files.
#
# USAGE: bash validate_videos.sh
#
# Requires ffprobe (part of ffmpeg): brew install ffmpeg

set -euo pipefail

BASE_DIR="/Users/a/Desktop/videomixer-deploy/assets"
VALID=0
INVALID=0
REMOVED=0

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

if ! command -v ffprobe &>/dev/null; then
    echo "ERROR: ffprobe not found. Install ffmpeg: brew install ffmpeg"
    exit 1
fi

log "Validating all .mp4 files in $BASE_DIR ..."

while IFS= read -r -d '' file; do
    codec=$(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of csv=p=0 "$file" 2>/dev/null)
    if [ -n "$codec" ]; then
        VALID=$((VALID + 1))
    else
        log "INVALID: $file"
        INVALID=$((INVALID + 1))
        # Uncomment the next line to auto-remove invalid files:
        # rm -f "$file" && REMOVED=$((REMOVED + 1)) && log "  -> Removed."
    fi
done < <(find "$BASE_DIR" -name "*.mp4" -print0)

log ""
log "============================================"
log "VALIDATION COMPLETE"
log "============================================"
log "Valid:   $VALID"
log "Invalid: $INVALID"
log "Removed: $REMOVED"
log "============================================"
