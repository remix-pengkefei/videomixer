#!/bin/bash

# Mixkit 视频素材批量下载脚本
# 下载免费可叠加的动效视频素材

BASE_DIR="/Users/fly/Desktop/VideoMixer/assets/overlays"
MIXKIT_BASE="https://assets.mixkit.co/videos"

echo "=========================================="
echo "从 Mixkit 下载动效视频素材"
echo "=========================================="

# 下载函数
download_mixkit() {
    local id="$1"
    local name="$2"
    local category="$3"
    local output="$BASE_DIR/$category/${name}_mixkit_${id}.mp4"

    if [ -f "$output" ]; then
        echo "跳过已存在: $(basename $output)"
        return
    fi

    echo "下载: $name (ID: $id) -> $category"
    curl -L -s --connect-timeout 30 --max-time 120 \
         -o "$output" \
         "$MIXKIT_BASE/$id/$id-720.mp4"

    if [ -f "$output" ] && [ $(stat -f%z "$output" 2>/dev/null || stat -c%s "$output" 2>/dev/null) -gt 10000 ]; then
        echo "  ✓ 完成: $(basename $output)"
    else
        echo "  ✗ 失败: $(basename $output)"
        rm -f "$output"
    fi
}

# ==========================================
# Particles 粒子效果
# ==========================================
echo ""
echo "=== 下载 Particles 粒子效果 ==="

download_mixkit "47285" "dust_floating_black" "particles"
download_mixkit "47356" "floating_particles_night" "particles"
download_mixkit "18140" "luminous_particles_space" "particles"
download_mixkit "46392" "stardust_golden" "particles"
download_mixkit "4407" "white_particles_black" "particles"
download_mixkit "18063" "light_waves_particles" "particles"
download_mixkit "18142" "luminous_particles_black" "particles"
download_mixkit "3465" "red_particles_falling" "particles"
download_mixkit "18138" "particles_floating" "particles"
download_mixkit "18139" "particles_rising" "particles"
download_mixkit "18141" "particles_swirl" "particles"
download_mixkit "47353" "particles_dust" "particles"
download_mixkit "47354" "particles_ambient" "particles"
download_mixkit "47357" "particles_glow" "particles"
download_mixkit "47358" "particles_motion" "particles"
download_mixkit "47359" "particles_flow" "particles"
download_mixkit "18064" "particles_wave" "particles"
download_mixkit "18065" "particles_stream" "particles"
download_mixkit "18066" "particles_scatter" "particles"
download_mixkit "18067" "particles_drift" "particles"
download_mixkit "24426" "bokeh_particles" "particles"
download_mixkit "4356" "bokeh_dots" "particles"
download_mixkit "18068" "particles_cosmic" "particles"
download_mixkit "18069" "particles_nebula" "particles"
download_mixkit "18070" "particles_galaxy" "particles"
download_mixkit "46393" "particles_golden" "particles"
download_mixkit "46394" "particles_dust_gold" "particles"
download_mixkit "46395" "particles_shimmer" "particles"
download_mixkit "4408" "particles_white_rising" "particles"
download_mixkit "4409" "particles_floating_up" "particles"

# ==========================================
# Smoke 烟雾效果
# ==========================================
echo ""
echo "=== 下载 Smoke 烟雾效果 ==="

download_mixkit "45298" "grey_smoke_black" "smoke"
download_mixkit "1960" "white_smoke_black" "smoke"
download_mixkit "1968" "black_bg_smoke" "smoke"
download_mixkit "1964" "smoke_motion" "smoke"
download_mixkit "50951" "smoke_trail_twirl" "smoke"
download_mixkit "1967" "smoke_effect_black" "smoke"
download_mixkit "1962" "plume_smoke_lower" "smoke"
download_mixkit "1963" "smoke_rising" "smoke"
download_mixkit "1965" "smoke_drifting" "smoke"
download_mixkit "1966" "smoke_flowing" "smoke"
download_mixkit "1969" "smoke_atmospheric" "smoke"
download_mixkit "1970" "smoke_dark" "smoke"
download_mixkit "1971" "smoke_thin" "smoke"
download_mixkit "1972" "smoke_dense" "smoke"
download_mixkit "50952" "smoke_swirl" "smoke"
download_mixkit "50953" "smoke_curl" "smoke"
download_mixkit "50954" "smoke_wave" "smoke"
download_mixkit "50955" "smoke_billow" "smoke"
download_mixkit "50956" "smoke_wisp" "smoke"
download_mixkit "50957" "smoke_ethereal" "smoke"
download_mixkit "12496" "light_smoke_dark" "smoke"
download_mixkit "5435" "abstract_smoke" "smoke"
download_mixkit "4867" "smoke_overlay" "smoke"
download_mixkit "4866" "smoke_wisps" "smoke"
download_mixkit "34474" "smoke_layer" "smoke"
download_mixkit "18052" "particle_explosion" "smoke"
download_mixkit "50958" "smoke_ambient" "smoke"
download_mixkit "50959" "smoke_soft" "smoke"
download_mixkit "50960" "smoke_elegant" "smoke"
download_mixkit "50961" "smoke_dramatic" "smoke"

# ==========================================
# Fire 火焰效果
# ==========================================
echo ""
echo "=== 下载 Fire 火焰效果 ==="

download_mixkit "52304" "flames_burst_black" "fire"
download_mixkit "4426" "lava_particles" "fire"
download_mixkit "45676" "bonfire_black" "fire"
download_mixkit "52284" "blazing_flames_black" "fire"
download_mixkit "52312" "flames_closeup_black" "fire"
download_mixkit "52299" "book_burns_dark" "fire"
download_mixkit "52300" "flames_rising" "fire"
download_mixkit "52301" "fire_burning" "fire"
download_mixkit "52302" "flames_dancing" "fire"
download_mixkit "52303" "fire_glow" "fire"
download_mixkit "52305" "flames_intense" "fire"
download_mixkit "52306" "fire_dramatic" "fire"
download_mixkit "52307" "flames_slow" "fire"
download_mixkit "52308" "fire_embers" "fire"
download_mixkit "52309" "flames_orange" "fire"
download_mixkit "52310" "fire_red" "fire"
download_mixkit "52311" "flames_yellow" "fire"
download_mixkit "4869" "fire_sparks_dark" "fire"
download_mixkit "28408" "fire_particles" "fire"
download_mixkit "4427" "embers_floating" "fire"
download_mixkit "4428" "sparks_flying" "fire"
download_mixkit "4429" "fire_ambient" "fire"
download_mixkit "4430" "flames_ambient" "fire"
download_mixkit "45677" "bonfire_flames" "fire"
download_mixkit "45678" "campfire_black" "fire"
download_mixkit "52313" "fire_elegant" "fire"
download_mixkit "52314" "flames_artistic" "fire"
download_mixkit "52315" "fire_abstract" "fire"
download_mixkit "52316" "flames_motion" "fire"
download_mixkit "52317" "fire_flow" "fire"

# ==========================================
# Sparkle 闪光效果
# ==========================================
echo ""
echo "=== 下载 Sparkle 闪光效果 ==="

download_mixkit "47961" "sparkles_black" "sparkle"
download_mixkit "18111" "christmas_bokeh" "sparkle"
download_mixkit "18151" "neon_sparkles_dark" "sparkle"
download_mixkit "21202" "golden_sparkles" "sparkle"
download_mixkit "12746" "starlight_tunnel" "sparkle"
download_mixkit "30607" "gold_glitter_sparks" "sparkle"
download_mixkit "30798" "sparks_black_surface" "sparkle"
download_mixkit "4414" "sparkler_sparks" "sparkle"
download_mixkit "30888" "golden_glitter_vertical" "sparkle"
download_mixkit "30749" "sparks_slow_motion" "sparkle"
download_mixkit "20743" "sparkler_burning" "sparkle"
download_mixkit "12725" "bengal_light_bokeh" "sparkle"
download_mixkit "18824" "sparkler_light" "sparkle"
download_mixkit "28406" "glitter_sparkle" "sparkle"
download_mixkit "46317" "golden_glitter" "sparkle"
download_mixkit "17890" "shine_sparkle" "sparkle"
download_mixkit "32750" "sparkle_overlay" "sparkle"
download_mixkit "30608" "glitter_gold_spin" "sparkle"
download_mixkit "30609" "sparkle_burst" "sparkle"
download_mixkit "30610" "glitter_cascade" "sparkle"
download_mixkit "30611" "sparkle_rain" "sparkle"
download_mixkit "30612" "glitter_fall" "sparkle"
download_mixkit "30613" "sparkle_float" "sparkle"
download_mixkit "30614" "glitter_drift" "sparkle"
download_mixkit "30615" "sparkle_swirl" "sparkle"
download_mixkit "18152" "sparkle_neon" "sparkle"
download_mixkit "18153" "sparkle_glow" "sparkle"
download_mixkit "18154" "sparkle_flash" "sparkle"
download_mixkit "18155" "sparkle_twinkle" "sparkle"
download_mixkit "18156" "sparkle_shimmer" "sparkle"

# ==========================================
# Snow 雪花效果
# ==========================================
echo ""
echo "=== 下载 Snow 雪花效果 ==="

download_mixkit "8468" "snow_falling_softly" "snow"
download_mixkit "12779" "snow_falling" "snow"
download_mixkit "20682" "snow_particles" "snow"
download_mixkit "8469" "snow_overlay" "snow"
download_mixkit "8470" "snow_gentle" "snow"
download_mixkit "8471" "snow_heavy" "snow"
download_mixkit "8472" "snow_light" "snow"
download_mixkit "8473" "snow_flurry" "snow"
download_mixkit "8474" "snow_blizzard" "snow"
download_mixkit "8475" "snow_drift" "snow"
download_mixkit "12780" "snow_night" "snow"
download_mixkit "12781" "snow_storm" "snow"
download_mixkit "12782" "snowflakes_falling" "snow"
download_mixkit "12783" "snow_ambient" "snow"
download_mixkit "12784" "snow_soft" "snow"
download_mixkit "20683" "snow_motion" "snow"
download_mixkit "20684" "snow_flow" "snow"
download_mixkit "20685" "snow_scatter" "snow"
download_mixkit "20686" "snow_swirl" "snow"
download_mixkit "20687" "snow_dance" "snow"
download_mixkit "41832" "snow_isolated_black" "snow"
download_mixkit "41833" "snowfall_black_bg" "snow"
download_mixkit "41834" "snow_dark_bg" "snow"
download_mixkit "41835" "snow_overlay_black" "snow"
download_mixkit "41836" "snow_particles_black" "snow"
download_mixkit "48851" "snow_falling_black" "snow"
download_mixkit "48852" "snowflakes_black" "snow"
download_mixkit "48853" "snow_gentle_black" "snow"
download_mixkit "48854" "snow_soft_black" "snow"
download_mixkit "48855" "snow_ambient_black" "snow"

# ==========================================
# Light 光效
# ==========================================
echo ""
echo "=== 下载 Light 光效 ==="

download_mixkit "38" "bokeh_blinking" "light"
download_mixkit "1833" "multicolor_flare" "light"
download_mixkit "34" "bokeh_white_blur" "light"
download_mixkit "33" "circles_light_bokeh" "light"
download_mixkit "1359" "purple_pink_bokeh" "light"
download_mixkit "44671" "neon_circles_glow" "light"
download_mixkit "30" "cars_lights_bokeh" "light"
download_mixkit "48013" "blue_light_leaks" "light"
download_mixkit "47282" "blue_crystal" "light"
download_mixkit "46237" "blurred_reflections" "light"
download_mixkit "46236" "blurred_spin" "light"
download_mixkit "48495" "bokeh_natural" "light"
download_mixkit "47283" "dark_blue_crystal" "light"
download_mixkit "47284" "crystal_light" "light"
download_mixkit "30728" "abstract_reflection" "light"
download_mixkit "55274" "light_leaks_effect" "light"
download_mixkit "55277" "light_leaks_bg" "light"
download_mixkit "21800" "abstract_speed_effect" "light"
download_mixkit "9131" "hexagonal_bokeh" "light"
download_mixkit "9174" "red_bokeh_floating" "light"
download_mixkit "31" "bokeh_blue" "light"
download_mixkit "32" "bokeh_warm" "light"
download_mixkit "35" "bokeh_colorful" "light"
download_mixkit "36" "bokeh_soft" "light"
download_mixkit "37" "bokeh_gentle" "light"
download_mixkit "39" "bokeh_ambient" "light"
download_mixkit "40" "bokeh_dreamy" "light"
download_mixkit "1834" "light_flare_motion" "light"
download_mixkit "1835" "light_leak_warm" "light"
download_mixkit "1836" "light_effect_glow" "light"

# ==========================================
# Abstract 抽象效果
# ==========================================
echo ""
echo "=== 下载 Abstract 抽象效果 ==="

download_mixkit "31497" "tunnel_black_cubes" "abstract"
download_mixkit "31562" "space_tunnel_fractal" "abstract"
download_mixkit "3524" "tv_glitch_texture" "abstract"
download_mixkit "4749" "abstract_waves" "abstract"
download_mixkit "41737" "digital_grid" "abstract"
download_mixkit "22375" "neon_lines" "abstract"
download_mixkit "31498" "abstract_tunnel" "abstract"
download_mixkit "31499" "abstract_vortex" "abstract"
download_mixkit "31500" "abstract_warp" "abstract"
download_mixkit "31501" "abstract_portal" "abstract"
download_mixkit "31502" "abstract_journey" "abstract"
download_mixkit "31503" "abstract_travel" "abstract"
download_mixkit "31504" "abstract_flight" "abstract"
download_mixkit "31505" "abstract_motion" "abstract"
download_mixkit "3525" "glitch_effect" "abstract"
download_mixkit "3526" "digital_noise" "abstract"
download_mixkit "3527" "static_texture" "abstract"
download_mixkit "3528" "video_distortion" "abstract"
download_mixkit "22376" "neon_glow" "abstract"
download_mixkit "22377" "neon_wave" "abstract"
download_mixkit "22378" "neon_pulse" "abstract"
download_mixkit "22379" "neon_flow" "abstract"
download_mixkit "41738" "digital_abstract" "abstract"
download_mixkit "41739" "tech_pattern" "abstract"
download_mixkit "41740" "cyber_grid" "abstract"
download_mixkit "41741" "matrix_effect" "abstract"
download_mixkit "4750" "wave_abstract" "abstract"
download_mixkit "4751" "flow_abstract" "abstract"
download_mixkit "4752" "motion_abstract" "abstract"
download_mixkit "4753" "lines_abstract" "abstract"

echo ""
echo "=========================================="
echo "下载完成! 统计结果:"
echo "=========================================="

for category in particles light smoke sparkle snow fire abstract; do
    count=$(ls -1 "$BASE_DIR/$category"/*.mp4 2>/dev/null | wc -l)
    echo "$category: $count 个文件"
done
