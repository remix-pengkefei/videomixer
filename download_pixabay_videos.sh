#!/bin/bash
#
# Pixabay Video Downloader for videomixer-deploy
#
# USAGE:
#   1. Get a free API key at https://pixabay.com/accounts/register/
#   2. Then go to https://pixabay.com/api/docs/#api_search_videos
#   3. Your key will be shown on that page
#   4. Run: PIXABAY_API_KEY="your-key-here" bash download_pixabay_videos.sh
#
# This script downloads free-for-commercial-use videos from Pixabay
# using their official API, respecting rate limits (100 req/min).

set -euo pipefail

API_KEY="${PIXABAY_API_KEY:-}"
BASE_DIR="/Users/a/Desktop/videomixer-deploy/assets"
API_URL="https://pixabay.com/api/videos/"
DELAY=0.7  # seconds between requests to stay under 100 req/min

if [ -z "$API_KEY" ]; then
    echo "ERROR: Please set PIXABAY_API_KEY environment variable."
    echo "  Get your free key at: https://pixabay.com/api/docs/"
    echo "  Then run: PIXABAY_API_KEY=\"your-key\" bash $0"
    exit 1
fi

# Counters
TOTAL_DOWNLOADED=0
TOTAL_FAILED=0

log() {
    echo "[$(date '+%H:%M:%S')] $*"
}

# download_videos QUERY TARGET_DIR PREFIX MAX_VIDEOS [EXTRA_PARAMS]
# Searches Pixabay and downloads videos to the target directory.
download_videos() {
    local query="$1"
    local target_dir="$2"
    local prefix="$3"
    local max_videos="${4:-30}"
    local extra_params="${5:-}"

    mkdir -p "$target_dir"

    local existing_count
    existing_count=$(find "$target_dir" -name "pixabay_${prefix}_*.mp4" 2>/dev/null | wc -l | tr -d ' ')

    log "Searching: '$query' -> $target_dir (prefix: $prefix, want: $max_videos, have: $existing_count)"

    if [ "$existing_count" -ge "$max_videos" ]; then
        log "  Already have $existing_count/$max_videos, skipping."
        return
    fi

    local remaining=$((max_videos - existing_count))
    local page=1
    local per_page=20  # Pixabay max per page
    local downloaded=0
    local counter=$((existing_count + 1))

    while [ "$downloaded" -lt "$remaining" ]; do
        sleep "$DELAY"

        local url="${API_URL}?key=${API_KEY}&q=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$query'))")&per_page=${per_page}&page=${page}&safesearch=true${extra_params}"

        local response
        response=$(curl -s --fail "$url" 2>/dev/null) || {
            log "  API request failed on page $page, stopping."
            break
        }

        local total_hits
        total_hits=$(echo "$response" | python3 -c "import sys,json; print(json.load(sys.stdin).get('totalHits',0))" 2>/dev/null)

        if [ "$total_hits" = "0" ]; then
            log "  No results for '$query'"
            break
        fi

        # Extract video URLs (medium size for balance of quality/size)
        # Falls back to small if medium unavailable
        local video_urls
        video_urls=$(echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
for hit in data.get('hits', []):
    videos = hit.get('videos', {})
    # Prefer medium (1280), then small (960), then tiny (640)
    for size in ['medium', 'small', 'tiny']:
        v = videos.get(size, {})
        url = v.get('url', '')
        if url:
            print(url)
            break
" 2>/dev/null)

        if [ -z "$video_urls" ]; then
            log "  No video URLs found on page $page, stopping."
            break
        fi

        while IFS= read -r video_url; do
            if [ "$downloaded" -ge "$remaining" ]; then
                break
            fi

            local filename="pixabay_${prefix}_$(printf '%03d' $counter).mp4"
            local filepath="${target_dir}/${filename}"

            if [ -f "$filepath" ]; then
                counter=$((counter + 1))
                continue
            fi

            sleep "$DELAY"
            if curl -sL --fail -o "$filepath" "$video_url" 2>/dev/null; then
                # Quick validation: check file is > 10KB
                local filesize
                filesize=$(stat -f%z "$filepath" 2>/dev/null || stat --printf="%s" "$filepath" 2>/dev/null || echo 0)
                if [ "$filesize" -gt 10240 ]; then
                    log "  Downloaded: $filename ($(( filesize / 1024 ))KB)"
                    downloaded=$((downloaded + 1))
                    TOTAL_DOWNLOADED=$((TOTAL_DOWNLOADED + 1))
                else
                    log "  WARN: $filename too small (${filesize}B), removing."
                    rm -f "$filepath"
                    TOTAL_FAILED=$((TOTAL_FAILED + 1))
                fi
            else
                log "  FAIL: Could not download $filename"
                rm -f "$filepath"
                TOTAL_FAILED=$((TOTAL_FAILED + 1))
            fi

            counter=$((counter + 1))
        done <<< "$video_urls"

        page=$((page + 1))

        # Safety: don't go past page 25 (500 videos max per query)
        if [ "$page" -gt 25 ]; then
            break
        fi
    done

    log "  Done: downloaded $downloaded new videos for '$query'"
}

# ============================================================
# PARTICLES (target: 200+ total)
# ============================================================
log "=== PARTICLES ==="
download_videos "particles black background"        "$BASE_DIR/particles" "particles"    25
download_videos "bokeh lights background"            "$BASE_DIR/particles" "bokeh"        25
download_videos "dust particles floating"            "$BASE_DIR/particles" "dust"         20
download_videos "sparkle glitter particles"          "$BASE_DIR/particles" "sparkle"      20
download_videos "snow falling black"                 "$BASE_DIR/particles" "snow"         20
download_videos "rain drops falling"                 "$BASE_DIR/particles" "rain"         15
download_videos "bubbles floating"                   "$BASE_DIR/particles" "bubbles"      15
download_videos "confetti falling"                   "$BASE_DIR/particles" "confetti"     15
download_videos "fireflies light"                    "$BASE_DIR/particles" "fireflies"    15
download_videos "smoke particles"                    "$BASE_DIR/particles" "smoke"        15
download_videos "fire sparks embers"                 "$BASE_DIR/particles" "fire"         15
download_videos "light particles glow"               "$BASE_DIR/particles" "lightglow"    15
download_videos "glitter shimmer"                    "$BASE_DIR/particles" "glitter"      15

# ============================================================
# TRANSITIONS (target: 200+ total)
# ============================================================
log "=== TRANSITIONS ==="
download_videos "transition effect"                  "$BASE_DIR/transitions" "transition"   30
download_videos "fade transition black"              "$BASE_DIR/transitions" "fade"         25
download_videos "wipe transition"                    "$BASE_DIR/transitions" "wipe"         25
download_videos "slide transition"                   "$BASE_DIR/transitions" "slide"        25
download_videos "zoom transition"                    "$BASE_DIR/transitions" "zoom"         25
download_videos "spin rotation transition"           "$BASE_DIR/transitions" "spin"         25
download_videos "glitch effect transition"           "$BASE_DIR/transitions" "glitch"       25
download_videos "blur transition"                    "$BASE_DIR/transitions" "blur"         25
download_videos "light leak transition"              "$BASE_DIR/transitions" "lightleak"    25

# ============================================================
# INTROS (target: 200+ total)
# ============================================================
log "=== INTROS ==="
download_videos "logo reveal animation"             "$BASE_DIR/intros" "logoreveal"   30
download_videos "title intro animation"             "$BASE_DIR/intros" "titleintro"   30
download_videos "particle intro"                    "$BASE_DIR/intros" "particleintro" 30
download_videos "light burst intro"                 "$BASE_DIR/intros" "lightburst"   30
download_videos "intro animation background"        "$BASE_DIR/intros" "introanim"    30
download_videos "cinematic intro"                   "$BASE_DIR/intros" "cinematic"    30
download_videos "neon intro animation"              "$BASE_DIR/intros" "neon"         25

# ============================================================
# OUTROS (target: 200+ total)
# ============================================================
log "=== OUTROS ==="
download_videos "end screen animation"              "$BASE_DIR/outros" "endscreen"    30
download_videos "closing animation"                 "$BASE_DIR/outros" "closing"      30
download_videos "outro animation"                   "$BASE_DIR/outros" "outro"        30
download_videos "subscribe animation"               "$BASE_DIR/outros" "subscribe"    30
download_videos "thank you animation"               "$BASE_DIR/outros" "thankyou"     30
download_videos "end card animation"                "$BASE_DIR/outros" "endcard"      30
download_videos "farewell animation"                "$BASE_DIR/outros" "farewell"     25

# ============================================================
# OVERLAYS - new subdirs (filling gaps)
# ============================================================
log "=== OVERLAYS ==="
download_videos "rain overlay black background"     "$BASE_DIR/overlays/rain"       "rain"       40
download_videos "dust overlay floating"             "$BASE_DIR/overlays/dust"       "dust"       40
download_videos "lens flare light"                  "$BASE_DIR/overlays/lens_flare" "lensflare"  40
download_videos "bokeh overlay lights"              "$BASE_DIR/overlays/bokeh"      "bokeh"      40
download_videos "color gradient background"         "$BASE_DIR/overlays/color"      "color"      40

# Fill existing overlay subdirs that may need more
download_videos "abstract background animation"     "$BASE_DIR/overlays/abstract"   "abstract2"  30
download_videos "confetti overlay celebration"       "$BASE_DIR/overlays/confetti"   "confetti2"  30
download_videos "fire flames black background"      "$BASE_DIR/overlays/fire"       "fire2"      30
download_videos "light rays overlay"                "$BASE_DIR/overlays/light"      "light2"     30
download_videos "particle overlay background"       "$BASE_DIR/overlays/particles"  "particle2"  30
download_videos "smoke fog overlay"                 "$BASE_DIR/overlays/smoke"      "smoke2"     30
download_videos "snowfall overlay"                  "$BASE_DIR/overlays/snow"       "snow2"      30
download_videos "sparkle overlay shimmer"           "$BASE_DIR/overlays/sparkle"    "sparkle2"   30

# ============================================================
# SUMMARY
# ============================================================
log ""
log "============================================"
log "DOWNLOAD COMPLETE"
log "============================================"
log "Total downloaded: $TOTAL_DOWNLOADED"
log "Total failed:     $TOTAL_FAILED"
log ""
log "Directory counts:"
for dir in particles transitions intros outros; do
    count=$(find "$BASE_DIR/$dir" -name "*.mp4" 2>/dev/null | wc -l | tr -d ' ')
    log "  $dir: $count videos"
done
for subdir in abstract confetti fire light particles smoke snow sparkle rain dust lens_flare bokeh color; do
    count=$(find "$BASE_DIR/overlays/$subdir" -name "*.mp4" 2>/dev/null | wc -l | tr -d ' ')
    log "  overlays/$subdir: $count videos"
done
overlay_total=$(find "$BASE_DIR/overlays" -name "*.mp4" 2>/dev/null | wc -l | tr -d ' ')
log "  overlays TOTAL: $overlay_total videos"
log "============================================"
