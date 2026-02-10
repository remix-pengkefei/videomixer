#!/bin/bash

# 视频素材批量下载脚本
# 下载免费可叠加的动效视频素材

BASE_DIR="/Users/fly/Desktop/VideoMixer/assets/overlays"

# 创建目录（如果不存在）
mkdir -p "$BASE_DIR"/{particles,light,smoke,sparkle,snow,fire,abstract}

echo "=========================================="
echo "开始下载动效视频素材"
echo "=========================================="

# 下载函数
download_video() {
    local url="$1"
    local output="$2"
    local category="$3"

    if [ -f "$output" ]; then
        echo "跳过已存在: $(basename $output)"
        return
    fi

    echo "下载: $(basename $output)"
    curl -L -s -o "$output" "$url" --connect-timeout 30 --max-time 120

    if [ -f "$output" ] && [ -s "$output" ]; then
        echo "  ✓ 完成: $(basename $output)"
    else
        echo "  ✗ 失败: $(basename $output)"
        rm -f "$output"
    fi
}

# ==========================================
# 从 Coverr 下载免费视频（黑底素材）
# ==========================================
echo ""
echo "=== 从 Coverr 下载 ==="

# Particles 粒子效果
download_video "https://storage.coverr.co/videos/coverr-particles-6053/1080p" "$BASE_DIR/particles/particles_floating_coverr_6053.mp4" "particles"
download_video "https://storage.coverr.co/videos/coverr-gold-particles-5936/1080p" "$BASE_DIR/particles/gold_particles_coverr_5936.mp4" "particles"

# ==========================================
# 从 Pixabay 下载免费视频
# ==========================================
echo ""
echo "=== 从 Pixabay 下载 ==="

# Particles
curl -L -s "https://cdn.pixabay.com/vimeo/258391671/particles-14580.mp4?width=1280" -o "$BASE_DIR/particles/blue_particles_pixabay_14580.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/313382467/particles-21282.mp4?width=1280" -o "$BASE_DIR/particles/gold_dust_pixabay_21282.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/319803267/particles-22379.mp4?width=1280" -o "$BASE_DIR/particles/floating_particles_pixabay_22379.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/274377943/particles-17185.mp4?width=1280" -o "$BASE_DIR/particles/dust_particles_pixabay_17185.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/268395977/particles-15931.mp4?width=1280" -o "$BASE_DIR/particles/sparkle_particles_pixabay_15931.mp4" &
wait

# Light effects
curl -L -s "https://cdn.pixabay.com/vimeo/196063108/bokeh-7115.mp4?width=1280" -o "$BASE_DIR/light/bokeh_lights_pixabay_7115.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/320195851/light-22460.mp4?width=1280" -o "$BASE_DIR/light/light_leak_pixabay_22460.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/225116549/light-10330.mp4?width=1280" -o "$BASE_DIR/light/flare_light_pixabay_10330.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/269159227/lens-16098.mp4?width=1280" -o "$BASE_DIR/light/lens_flare_pixabay_16098.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/278899469/bokeh-17755.mp4?width=1280" -o "$BASE_DIR/light/bokeh_golden_pixabay_17755.mp4" &
wait

# Smoke
curl -L -s "https://cdn.pixabay.com/vimeo/158619012/smoke-4091.mp4?width=1280" -o "$BASE_DIR/smoke/white_smoke_pixabay_4091.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/208949656/smoke-8173.mp4?width=1280" -o "$BASE_DIR/smoke/rising_smoke_pixabay_8173.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/253977019/smoke-13967.mp4?width=1280" -o "$BASE_DIR/smoke/colored_smoke_pixabay_13967.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/163315108/smoke-4540.mp4?width=1280" -o "$BASE_DIR/smoke/dense_smoke_pixabay_4540.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/263022167/smoke-15052.mp4?width=1280" -o "$BASE_DIR/smoke/swirl_smoke_pixabay_15052.mp4" &
wait

# Sparkle
curl -L -s "https://cdn.pixabay.com/vimeo/240437073/sparkle-12419.mp4?width=1280" -o "$BASE_DIR/sparkle/gold_sparkle_pixabay_12419.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/257665947/glitter-14481.mp4?width=1280" -o "$BASE_DIR/sparkle/glitter_fall_pixabay_14481.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/234959879/sparkle-11726.mp4?width=1280" -o "$BASE_DIR/sparkle/star_sparkle_pixabay_11726.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/197282116/stars-7239.mp4?width=1280" -o "$BASE_DIR/sparkle/stars_twinkling_pixabay_7239.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/284022620/glitter-18260.mp4?width=1280" -o "$BASE_DIR/sparkle/silver_glitter_pixabay_18260.mp4" &
wait

# Snow
curl -L -s "https://cdn.pixabay.com/vimeo/195269387/snow-7009.mp4?width=1280" -o "$BASE_DIR/snow/falling_snow_pixabay_7009.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/243553988/snow-12730.mp4?width=1280" -o "$BASE_DIR/snow/heavy_snow_pixabay_12730.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/193792115/snow-6858.mp4?width=1280" -o "$BASE_DIR/snow/light_snow_pixabay_6858.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/349419259/snowflakes-27268.mp4?width=1280" -o "$BASE_DIR/snow/snowflakes_falling_pixabay_27268.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/200261355/winter-7543.mp4?width=1280" -o "$BASE_DIR/snow/winter_snow_pixabay_7543.mp4" &
wait

# Fire
curl -L -s "https://cdn.pixabay.com/vimeo/158619081/fire-4093.mp4?width=1280" -o "$BASE_DIR/fire/flames_pixabay_4093.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/310119866/fire-20639.mp4?width=1280" -o "$BASE_DIR/fire/burning_fire_pixabay_20639.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/236022143/fire-11876.mp4?width=1280" -o "$BASE_DIR/fire/ember_fire_pixabay_11876.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/214629591/fire-8838.mp4?width=1280" -o "$BASE_DIR/fire/hot_fire_pixabay_8838.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/265426691/fire-15335.mp4?width=1280" -o "$BASE_DIR/fire/flame_burst_pixabay_15335.mp4" &
wait

# Abstract
curl -L -s "https://cdn.pixabay.com/vimeo/300888970/abstract-19659.mp4?width=1280" -o "$BASE_DIR/abstract/wave_abstract_pixabay_19659.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/243127888/abstract-12670.mp4?width=1280" -o "$BASE_DIR/abstract/lines_abstract_pixabay_12670.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/289891795/abstract-18790.mp4?width=1280" -o "$BASE_DIR/abstract/shapes_abstract_pixabay_18790.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/291411339/abstract-18965.mp4?width=1280" -o "$BASE_DIR/abstract/motion_abstract_pixabay_18965.mp4" &
curl -L -s "https://cdn.pixabay.com/vimeo/245993082/abstract-12963.mp4?width=1280" -o "$BASE_DIR/abstract/flow_abstract_pixabay_12963.mp4" &
wait

echo ""
echo "=== 第一批下载完成 ==="
echo ""

# 统计下载结果
for category in particles light smoke sparkle snow fire abstract; do
    count=$(ls -1 "$BASE_DIR/$category"/*.mp4 2>/dev/null | wc -l)
    echo "$category: $count 个文件"
done

echo ""
echo "=========================================="
echo "下载完成!"
echo "=========================================="
