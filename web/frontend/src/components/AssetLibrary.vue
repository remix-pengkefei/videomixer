<template>
  <div class="asset-library">
    <!-- Loading -->
    <div v-if="loading" class="asset-loading">
      <div class="spinner"></div>
      <div>加载素材数据...</div>
    </div>

    <template v-else>
      <!-- Overview Cards -->
      <div class="asset-grid">
        <div class="asset-overview-card">
          <div class="asset-card-icon">🎨</div>
          <div class="asset-card-title">贴纸素材</div>
          <div class="asset-card-number">{{ data?.stickers?.total?.toLocaleString() || 0 }}</div>
          <div class="asset-card-label">张 PNG 图片</div>
        </div>
        <div class="asset-overview-card">
          <div class="asset-card-icon">✨</div>
          <div class="asset-card-title">闪光素材</div>
          <div class="asset-card-number">{{ data?.sparkles?.total?.toLocaleString() || 0 }}</div>
          <div class="asset-card-label">个闪光效果</div>
        </div>
      </div>

      <!-- Sticker Categories -->
      <div class="asset-section">
        <div class="asset-section-title">贴纸分类</div>
        <div class="asset-breakdown-grid">
          <div
            v-for="(count, name) in data?.stickers?.categories || {}"
            :key="name"
            class="asset-breakdown-item"
          >
            <div class="breakdown-name">{{ name }}</div>
            <div class="breakdown-count">{{ count.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Sparkle Styles -->
      <div class="asset-section">
        <div class="asset-section-title">闪光风格</div>
        <div class="asset-breakdown-grid">
          <div
            v-for="(count, style) in data?.sparkles?.styles || {}"
            :key="style"
            class="asset-breakdown-item"
          >
            <div class="breakdown-name">{{ styleLabel(style) }}</div>
            <div class="breakdown-count">{{ count.toLocaleString() }}</div>
          </div>
        </div>
      </div>

      <!-- Effect Presets -->
      <div class="asset-section">
        <div class="asset-section-title">效果预设</div>
        <div class="effect-grid">
          <div v-for="item in effectItems" :key="item.key" class="effect-item">
            <span class="effect-count">{{ data?.effects?.[item.key] || 0 }}</span>
            <span class="effect-label">{{ item.label }}</span>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const data = ref(null)

const effectItems = [
  { key: 'color_schemes', label: '配色方案' },
  { key: 'mask_styles', label: '遮罩样式' },
  { key: 'particle_styles', label: '粒子特效' },
  { key: 'decoration_styles', label: '装饰布局' },
  { key: 'border_styles', label: '边框样式' },
  { key: 'text_styles', label: '文字效果' },
  { key: 'audio_effects', label: '音频调整' },
  { key: 'color_presets', label: '调色预设' },
  { key: 'lut_presets', label: 'LUT调色' },
  { key: 'speed_ramps', label: '变速曲线' },
  { key: 'lens_effects', label: '镜头效果' },
  { key: 'glitch_effects', label: '故障特效' },
]

function styleLabel(style) {
  const map = { gold: '金色', pink: '粉色', warm: '暖色', cool: '冷色', mixed: '混合' }
  return map[style] || style
}

onMounted(async () => {
  try {
    const res = await fetch('/api/assets/overview')
    data.value = await res.json()
  } catch (e) {
    console.error('Failed to load asset data:', e)
  } finally {
    loading.value = false
  }
})
</script>
