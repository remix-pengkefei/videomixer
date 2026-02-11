<template>
  <div
    v-for="cat in categories"
    :key="cat.folder"
    class="category-card"
  >
    <!-- Card Header -->
    <div class="category-card-header">
      <div class="category-info-block">
        <div class="category-card-name">{{ cat.display_name || cat.folder }}</div>
        <div class="category-card-count">{{ cat.video_count }} 个视频</div>
      </div>

      <span class="strategy-tag" :class="cat.strategy">
        {{ strategyLabel(cat.strategy) }}
      </span>

      <select
        :value="cat.strategy"
        :disabled="taskActive"
        @change="$emit('updateStrategy', cat.folder, $event.target.value)"
        class="category-strategy-select"
      >
        <option
          v-for="s in strategies"
          :key="s.id"
          :value="s.id"
        >
          {{ s.name }}
        </option>
      </select>

      <button
        class="btn-expand"
        :disabled="taskActive"
        @click="toggleExpand(cat.folder)"
      >
        {{ expandedFolders.has(cat.folder) ? '收起 ▴' : '配置 ▾' }}
      </button>
    </div>

    <!-- Video File List -->
    <div class="category-files">
      <div
        v-for="f in cat.files"
        :key="f"
        class="category-file-row"
      >
        <span class="category-file-icon">&#9654;</span>
        <span class="category-file-name">{{ f }}</span>
        <span class="strategy-tag-sm" :class="cat.strategy">
          {{ strategyLabel(cat.strategy) }}
        </span>
      </div>
    </div>

    <!-- Expanded Config Panel -->
    <div
      v-if="expandedFolders.has(cat.folder)"
      class="config-panel"
    >
      <div class="config-row">
        <label class="config-label">贴纸数量</label>
        <input
          type="range"
          class="range-slider"
          min="5"
          max="30"
          :value="getConfig(cat.folder).sticker_count"
          @input="updateConfig(cat.folder, 'sticker_count', +$event.target.value)"
        />
        <span class="config-value">{{ getConfig(cat.folder).sticker_count }}</span>
      </div>

      <div class="config-row">
        <label class="config-label">闪光数量</label>
        <input
          type="range"
          class="range-slider"
          min="1"
          max="10"
          :value="getConfig(cat.folder).sparkle_count"
          @input="updateConfig(cat.folder, 'sparkle_count', +$event.target.value)"
        />
        <span class="config-value">{{ getConfig(cat.folder).sparkle_count }}</span>
      </div>

      <div class="config-row">
        <label class="config-label">闪光风格</label>
        <select
          class="config-select"
          :value="getConfig(cat.folder).sparkle_style"
          @change="updateConfig(cat.folder, 'sparkle_style', $event.target.value)"
        >
          <option v-for="s in sparkleStyles" :key="s.value" :value="s.value">
            {{ s.label }}
          </option>
        </select>
      </div>

      <div class="config-row">
        <label class="config-label">配色方案</label>
        <select
          class="config-select"
          :value="getConfig(cat.folder).color_scheme"
          @change="updateConfig(cat.folder, 'color_scheme', $event.target.value)"
        >
          <option v-for="c in colorSchemes" :key="c.value" :value="c.value">
            {{ c.label }}
          </option>
        </select>
      </div>

      <div class="config-row config-toggles-label">
        <label class="config-label">效果开关</label>
      </div>
      <div class="config-toggles">
        <label class="toggle-item" v-for="toggle in effectToggles" :key="toggle.key">
          <div
            class="toggle-switch"
            :class="{ on: getConfig(cat.folder)[toggle.key] }"
            @click="updateConfig(cat.folder, toggle.key, !getConfig(cat.folder)[toggle.key])"
          >
            <div class="toggle-knob"></div>
          </div>
          <span class="toggle-label">{{ toggle.label }}</span>
        </label>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  categories: Array,
  strategies: Array,
  configs: Object,
  taskActive: { type: Boolean, default: false },
})

const emit = defineEmits(['updateStrategy', 'updateConfig'])

const expandedFolders = ref(new Set())

const sparkleStyles = [
  { value: 'gold', label: '金色' },
  { value: 'pink', label: '粉色' },
  { value: 'warm', label: '暖色' },
  { value: 'cool', label: '冷色' },
  { value: 'mixed', label: '混合' },
]

const colorSchemes = [
  { value: 'random', label: '随机' },
  { value: '金色暖调', label: '金色暖调' },
  { value: '冷色优雅', label: '冷色优雅' },
  { value: '莫兰迪', label: '莫兰迪' },
  { value: '粉紫甜美', label: '粉紫甜美' },
  { value: '自然绿意', label: '自然绿意' },
  { value: '赛博朋克', label: '赛博朋克' },
  { value: '复古怀旧', label: '复古怀旧' },
  { value: '海洋蓝调', label: '海洋蓝调' },
]

const effectToggles = [
  { key: 'enable_particles', label: '粒子特效' },
  { key: 'enable_decorations', label: '装饰效果' },
  { key: 'enable_border', label: '边框' },
  { key: 'enable_color_preset', label: '调色滤镜' },
  { key: 'enable_audio_fx', label: '音频调整' },
]

function strategyLabel(id) {
  const map = { handwriting: '手写', emotional: '情感', health: '养生' }
  return map[id] || id
}

function getConfig(folder) {
  return props.configs?.[folder] || {}
}

function toggleExpand(folder) {
  const s = new Set(expandedFolders.value)
  if (s.has(folder)) { s.delete(folder) } else { s.add(folder) }
  expandedFolders.value = s
}

function updateConfig(folder, key, value) {
  emit('updateConfig', folder, key, value)
}
</script>
