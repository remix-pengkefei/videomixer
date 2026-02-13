#!/bin/bash
# Scan all asset directories and generate real counts for the website
# Run this after adding/removing assets to update the displayed counts

BASE="$(cd "$(dirname "$0")" && pwd)"
ASSETS="$BASE/assets"
OUT="$BASE/web/frontend/dist/asset-counts.json"

count_files() {
    find "$1" -type f 2>/dev/null | wc -l | tr -d ' '
}

# Count sticker categories
sticker_cats=""
if [ -d "$ASSETS/stickers" ]; then
    for dir in "$ASSETS/stickers"/*/; do
        [ -d "$dir" ] || continue
        name=$(basename "$dir")
        cnt=$(count_files "$dir")
        [ "$cnt" -gt 0 ] && sticker_cats="$sticker_cats\"$name\":$cnt,"
    done
    sticker_cats="${sticker_cats%,}"
fi
sticker_total=$(count_files "$ASSETS/stickers")

# Count sparkle styles
sparkle_styles=""
if [ -d "$ASSETS/sparkles" ]; then
    for dir in "$ASSETS/sparkles"/*/; do
        [ -d "$dir" ] || continue
        name=$(basename "$dir")
        cnt=$(count_files "$dir")
        [ "$cnt" -gt 0 ] && sparkle_styles="$sparkle_styles\"$name\":$cnt,"
    done
    sparkle_styles="${sparkle_styles%,}"
fi
sparkle_total=$(count_files "$ASSETS/sparkles")

# Count overlay categories
overlay_cats=""
if [ -d "$ASSETS/overlays" ]; then
    for dir in "$ASSETS/overlays"/*/; do
        [ -d "$dir" ] || continue
        name=$(basename "$dir")
        cnt=$(count_files "$dir")
        [ "$cnt" -gt 0 ] && overlay_cats="$overlay_cats\"$name\":$cnt,"
    done
    overlay_cats="${overlay_cats%,}"
fi
overlay_total=$(count_files "$ASSETS/overlays")

# Count other categories
filler_total=$(count_files "$ASSETS/filler_videos")
titles_total=$(count_files "$ASSETS/titles")
animated_total=$(count_files "$ASSETS/animated")
frames_total=$(count_files "$ASSETS/frames")
png_total=$(count_files "$ASSETS/png_downloads")
mix_stickers_total=$(count_files "$ASSETS/mix_stickers")
particles_total=$(count_files "$ASSETS/particles")
intros_total=$(count_files "$ASSETS/intros")
outros_total=$(count_files "$ASSETS/outros")
transitions_total=$(count_files "$ASSETS/transitions")

# Generate JSON
cat > "$OUT" << ENDJSON
{
  "stickers": {
    "total": $sticker_total,
    "categories": {$sticker_cats}
  },
  "sparkles": {
    "total": $sparkle_total,
    "styles": {$sparkle_styles}
  },
  "overlays": {
    "total": $overlay_total,
    "categories": {$overlay_cats}
  },
  "filler_videos": {"total": $filler_total},
  "titles": {"total": $titles_total},
  "animated": {"total": $animated_total},
  "frames": {"total": $frames_total},
  "png_downloads": {"total": $png_total},
  "mix_stickers": {"total": $mix_stickers_total},
  "particles": {"total": $particles_total},
  "intros": {"total": $intros_total},
  "outros": {"total": $outros_total},
  "transitions": {"total": $transitions_total},
  "effects": {
    "color_schemes": 8,
    "mask_styles": 5,
    "particle_styles": 6,
    "decoration_styles": 5,
    "border_styles": 6,
    "text_styles": 6,
    "audio_effects": 5,
    "color_presets": 8,
    "lut_presets": 10,
    "speed_ramps": 7,
    "lens_effects": 9,
    "glitch_effects": 8
  },
  "updated_at": "$(date '+%Y-%m-%d %H:%M:%S')"
}
ENDJSON

echo "Asset counts updated: $OUT"
echo "Stickers: $sticker_total | Sparkles: $sparkle_total | Overlays: $overlay_total"
echo "Particles: $particles_total | Intros: $intros_total | Outros: $outros_total | Transitions: $transitions_total"
echo "Filler: $filler_total | Titles: $titles_total | Animated: $animated_total | Frames: $frames_total"
