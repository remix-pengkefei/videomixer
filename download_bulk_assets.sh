#!/bin/bash
# ============================================================================
# BULK ASSET DOWNLOADER
# Downloads free, openly-licensed bulk asset packs for videomixer
# ============================================================================

set -e
BASE_DIR="$HOME/Desktop/videomixer-deploy/assets"
TMP_DIR="/tmp/videomixer_bulk_downloads"
mkdir -p "$TMP_DIR"

echo "============================================"
echo " Bulk Asset Downloader for VideoMixer"
echo "============================================"
echo ""

# -------------------------------------------------------
# 1. SPARKLE/GLITTER PNG PACKS
# -------------------------------------------------------
download_sparkles() {
    echo "=== Downloading Sparkle/Glitter Packs ==="

    # OpenMoji release has some star/sparkle emoji
    echo "[1/2] Already have 22,000+ sparkle PNGs in assets/sparkles/"
    echo "  For MORE sparkles, generate them with: python3 generate_sparkles.py"
    echo ""

    # Suggestion: Use the Pixabay API for bulk bokeh/sparkle images
    echo "[2/2] For additional sparkle/bokeh textures:"
    echo "  - ResourceBoy 200+ Lens Flares: https://resourceboy.com/textures/lens-flare-overlays/"
    echo "  - ResourceBoy 250 Light Leaks: https://resourceboy.com/textures/light-leak-overlays/"
    echo "  - FixThePhoto 438 Bokeh Overlays: https://fixthephoto.com/photoshop-bokeh-overlay-free"
    echo "  - FixThePhoto 110 Glitter Overlays: https://fixthephoto.com/glitter-overlay"
    echo "  (These require browser download due to anti-bot protection)"
    echo ""
}

# -------------------------------------------------------
# 2. VIDEO OVERLAY EFFECT PACKS
# -------------------------------------------------------
download_overlays() {
    echo "=== Video Overlay Sources ==="
    echo "Already have 3,243 overlay files."
    echo ""
    echo "For MORE video overlays (require browser/manual download):"
    echo "  - FXElements 130+ Free VFX: https://www.fxelements.com/free"
    echo "  - ActionVFX Free Collection (650+ assets): https://www.actionvfx.com/collections/free-vfx/category"
    echo "  - iNeedFX Free Library: https://ineedfx.com/"
    echo "  - CinePacks Free Packs: https://cinepacks.store/collections/free-packs"
    echo "  - MyCreativeFX 3000+ VFX: https://mycreativefx.com/"
    echo "  - Videezy 5000+ overlays: https://www.videezy.com/free-video/overlay-effect"
    echo "  - Pixabay 233+ VFX clips (CC0): https://pixabay.com/videos/search/vfx/"
    echo ""
}

# -------------------------------------------------------
# 3. STICKER/EMOJI COLLECTIONS (GitHub repos)
# -------------------------------------------------------
download_stickers() {
    echo "=== Downloading Sticker/Icon Collections ==="

    # Twitter Twemoji (CC-BY 4.0, 3689 emoji)
    if [ ! -d "$BASE_DIR/stickers/emoji_twemoji_72" ] || [ "$(find "$BASE_DIR/stickers/emoji_twemoji_72" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[1/6] Downloading Twitter Twemoji (3689 emoji, CC-BY 4.0)..."
        git clone --depth 1 https://github.com/twitter/twemoji.git "$TMP_DIR/twemoji" 2>/dev/null
        mkdir -p "$BASE_DIR/stickers/emoji_twemoji_72"
        cp "$TMP_DIR/twemoji/assets/72x72/"*.png "$BASE_DIR/stickers/emoji_twemoji_72/"
        rm -rf "$TMP_DIR/twemoji"
        echo "  Done: $(ls "$BASE_DIR/stickers/emoji_twemoji_72/"*.png | wc -l) files"
    else
        echo "[1/6] Twemoji already downloaded ($(find "$BASE_DIR/stickers/emoji_twemoji_72" -name '*.png' | wc -l) files)"
    fi

    # GitHub Emojis (1936 emoji)
    if [ ! -d "$BASE_DIR/stickers/emoji_github" ] || [ "$(find "$BASE_DIR/stickers/emoji_github" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[2/6] Downloading GitHub Emojis (1936 emoji)..."
        git clone --depth 1 https://github.com/pranabdas/github-emojis.git "$TMP_DIR/github-emojis" 2>/dev/null
        mkdir -p "$BASE_DIR/stickers/emoji_github"
        cp "$TMP_DIR/github-emojis/assets/png/"*.png "$BASE_DIR/stickers/emoji_github/"
        rm -rf "$TMP_DIR/github-emojis"
        echo "  Done: $(ls "$BASE_DIR/stickers/emoji_github/"*.png | wc -l) files"
    else
        echo "[2/6] GitHub emojis already downloaded ($(find "$BASE_DIR/stickers/emoji_github" -name '*.png' | wc -l) files)"
    fi

    # OpenMoji (CC BY-SA 4.0, 4292 emoji)
    if [ ! -d "$BASE_DIR/stickers/emoji_openmoji_72" ] || [ "$(find "$BASE_DIR/stickers/emoji_openmoji_72" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[3/6] Downloading OpenMoji (4292 emoji, CC BY-SA 4.0)..."
        curl -sL -o "$TMP_DIR/openmoji-72x72-color.zip" \
            "https://github.com/hfg-gmuend/openmoji/releases/latest/download/openmoji-72x72-color.zip"
        mkdir -p "$BASE_DIR/stickers/emoji_openmoji_72"
        unzip -o "$TMP_DIR/openmoji-72x72-color.zip" -d "$BASE_DIR/stickers/emoji_openmoji_72/" >/dev/null 2>&1
        rm -f "$TMP_DIR/openmoji-72x72-color.zip"
        echo "  Done: $(ls "$BASE_DIR/stickers/emoji_openmoji_72/"*.png 2>/dev/null | wc -l) files"
    else
        echo "[3/6] OpenMoji already downloaded ($(find "$BASE_DIR/stickers/emoji_openmoji_72" -name '*.png' | wc -l) files)"
    fi

    # Google Noto Emoji 128px (Apache 2.0, 3768 emoji)
    if [ ! -d "$BASE_DIR/stickers/emoji_noto_128" ] || [ "$(find "$BASE_DIR/stickers/emoji_noto_128" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[4/6] Downloading Google Noto Emoji 128px (3768 emoji, Apache 2.0)..."
        git clone --depth 1 --filter=blob:none --sparse \
            https://github.com/googlefonts/noto-emoji.git "$TMP_DIR/noto-emoji" 2>/dev/null
        cd "$TMP_DIR/noto-emoji" && git sparse-checkout set "png/128" 2>/dev/null
        mkdir -p "$BASE_DIR/stickers/emoji_noto_128"
        cp "$TMP_DIR/noto-emoji/png/128/"*.png "$BASE_DIR/stickers/emoji_noto_128/" 2>/dev/null
        rm -rf "$TMP_DIR/noto-emoji"
        echo "  Done: $(ls "$BASE_DIR/stickers/emoji_noto_128/"*.png 2>/dev/null | wc -l) files"
    else
        echo "[4/6] Noto emoji already downloaded ($(find "$BASE_DIR/stickers/emoji_noto_128" -name '*.png' | wc -l) files)"
    fi

    # Game Icons (CC BY/CC0, 4229 SVG -> PNG)
    if [ ! -d "$BASE_DIR/stickers/game_icons" ] || [ "$(find "$BASE_DIR/stickers/game_icons" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[5/6] Downloading Game Icons (4229 icons, CC BY/CC0)..."
        git clone --depth 1 https://github.com/game-icons/icons.git "$TMP_DIR/game-icons" 2>/dev/null
        mkdir -p "$BASE_DIR/stickers/game_icons"
        find "$TMP_DIR/game-icons" -name "*.svg" -type f | while read svg; do
            basename_no_ext=$(basename "$svg" .svg)
            dirname_part=$(basename "$(dirname "$svg")")
            convert "$svg" -resize 128x128 -background transparent -gravity center -extent 128x128 \
                "$BASE_DIR/stickers/game_icons/${dirname_part}_${basename_no_ext}.png" 2>/dev/null
        done
        rm -rf "$TMP_DIR/game-icons"
        echo "  Done: $(ls "$BASE_DIR/stickers/game_icons/"*.png 2>/dev/null | wc -l) files"
    else
        echo "[5/6] Game icons already downloaded ($(find "$BASE_DIR/stickers/game_icons" -name '*.png' | wc -l) files)"
    fi

    # Simple Icons (CC0, 3397 brand icons)
    if [ ! -d "$BASE_DIR/stickers/simple_icons" ] || [ "$(find "$BASE_DIR/stickers/simple_icons" -name '*.png' | wc -l)" -lt 100 ]; then
        echo "[6/6] Downloading Simple Icons (3397 brand icons, CC0)..."
        git clone --depth 1 https://github.com/simple-icons/simple-icons.git "$TMP_DIR/simple-icons" 2>/dev/null
        mkdir -p "$BASE_DIR/stickers/simple_icons"
        for svg in "$TMP_DIR/simple-icons/icons/"*.svg; do
            basename_no_ext=$(basename "$svg" .svg)
            convert "$svg" -resize 128x128 -background transparent -gravity center -extent 128x128 \
                "$BASE_DIR/stickers/simple_icons/$basename_no_ext.png" 2>/dev/null
        done
        rm -rf "$TMP_DIR/simple-icons"
        echo "  Done: $(ls "$BASE_DIR/stickers/simple_icons/"*.png 2>/dev/null | wc -l) files"
    else
        echo "[6/6] Simple icons already downloaded ($(find "$BASE_DIR/stickers/simple_icons" -name '*.png' | wc -l) files)"
    fi
    echo ""
}

# -------------------------------------------------------
# 4. ANIMATED GIF COLLECTIONS
# -------------------------------------------------------
download_animated() {
    echo "=== Animated GIF Sources ==="
    echo "Already have 608 animated files."
    echo ""
    echo "For MORE animated GIFs:"
    echo "  - LottieFiles free stickers (GIF/Lottie): https://lottiefiles.com/free-animations/sticker"
    echo "  - Pixabay GIF stickers (CC0): https://pixabay.com/gifs/"
    echo "  - Microsoft Animated Fluent Emojis: https://github.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis"
    echo "    (Large repo ~5GB, clone with: git clone --depth 1 https://github.com/Tarikul-Islam-Anik/Animated-Fluent-Emojis.git)"
    echo "  - Microsoft fluentui-emoji-animated: https://github.com/microsoft/fluentui-emoji-animated"
    echo "    (Uses Git LFS, ~5GB)"
    echo ""
}

# -------------------------------------------------------
# 5. FRAME/BORDER PNG COLLECTIONS
# -------------------------------------------------------
download_frames() {
    echo "=== Frame/Border Sources ==="
    echo "Already have 770 frame files."
    echo ""
    echo "For MORE frames/borders:"
    echo "  - LibRetro Overlay Borders: https://github.com/libretro/overlay-borders"
    echo "    (git clone --depth 1 https://github.com/libretro/overlay-borders.git)"
    echo "  - PNG Packs Borders & Frames: https://www.pngpacks.com/category/borders-frames-png"
    echo "  - FreePNGimg Decorative Borders (1299 PNGs): https://freepngimg.com/miscellaneous/decorative-border"
    echo "  - CleanPNG Borders: https://www.cleanpng.com/free/border.html"
    echo ""
}

# -------------------------------------------------------
# MAIN
# -------------------------------------------------------
echo "Starting bulk downloads..."
echo ""

download_sparkles
download_overlays
download_stickers
download_animated
download_frames

# Final counts
echo "============================================"
echo " FINAL ASSET COUNTS"
echo "============================================"
echo "Stickers: $(find "$BASE_DIR/stickers" -type f \( -name '*.png' -o -name '*.jpg' -o -name '*.webp' \) | wc -l)"
echo "Sparkles: $(find "$BASE_DIR/sparkles" -type f | wc -l)"
echo "Overlays: $(find "$BASE_DIR/overlays" -type f | wc -l)"
echo "Animated: $(find "$BASE_DIR/animated" -type f | wc -l)"
echo "Frames:   $(find "$BASE_DIR/frames" -type f | wc -l)"
echo ""
echo "Cleanup..."
rm -rf "$TMP_DIR"
echo "Done!"
