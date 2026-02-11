<template>
  <div class="strategy-page">
    <div class="strategy-page-header">
      <h2 class="strategy-page-title">策略配置</h2>
      <p class="strategy-page-desc">设置各类混剪的默认参数，新任务将自动使用这些配置</p>
    </div>

    <div
      v-for="s in strategyList"
      :key="s.id"
      class="strategy-card"
    >
      <div class="strategy-card-header">
        <div class="strategy-card-info">
          <div class="strategy-card-name">{{ s.name }}</div>
          <div class="strategy-card-desc">{{ s.description }}</div>
        </div>
        <button
          class="btn-expand"
          @click="toggleExpand(s.id)"
        >
          {{ expanded.has(s.id) ? '收起 ▴' : '展开 ▾' }}
        </button>
      </div>

      <div v-if="expanded.has(s.id)" class="config-panel">
        <div class="config-row">
          <label class="config-label">贴纸数量</label>
          <input
            type="range"
            class="range-slider"
            min="5"
            max="30"
            :value="getVal(s.id, 'sticker_count')"
            @input="setVal(s.id, 'sticker_count', +$event.target.value)"
          />
          <span class="config-value">{{ getVal(s.id, 'sticker_count') }}</span>
        </div>

        <div class="config-row">
          <label class="config-label">闪光数量</label>
          <input
            type="range"
            class="range-slider"
            min="1"
            max="10"
            :value="getVal(s.id, 'sparkle_count')"
            @input="setVal(s.id, 'sparkle_count', +$event.target.value)"
          />
          <span class="config-value">{{ getVal(s.id, 'sparkle_count') }}</span>
        </div>

        <div class="config-row">
          <label class="config-label">闪光风格</label>
          <select
            class="config-select"
            :value="getVal(s.id, 'sparkle_style')"
            @change="setVal(s.id, 'sparkle_style', $event.target.value)"
          >
            <option v-for="opt in sparkleStyles" :key="opt.value" :value="opt.value">
              {{ opt.label }}
            </option>
          </select>
        </div>

        <div class="config-row">
          <label class="config-label">配色方案</label>
          <select
            class="config-select"
            :value="getVal(s.id, 'color_scheme')"
            @change="setVal(s.id, 'color_scheme', $event.target.value)"
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
              :class="{ on: getVal(s.id, toggle.key) }"
              @click="setVal(s.id, toggle.key, !getVal(s.id, toggle.key))"
            >
              <div class="toggle-knob"></div>
            </div>
            <span class="toggle-label">{{ toggle.label }}</span>
          </label>
        </div>

        <div class="strategy-save-row">
          <button class="btn-recommend" @click="resetToDefaults(s.id)">推荐设置</button>
          <span v-if="saveStatus[s.id]" class="save-status">{{ saveStatus[s.id] }}</span>
          <button class="btn-save" @click="save(s.id)">保存</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const props = defineProps({
  strategies: Array,
  globalConfig: Object,
})

const emit = defineEmits(['saved'])

const expanded = ref(new Set(['handwriting']))
const local = reactive({})
const saveStatus = reactive({})

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

const strategyList = [
  { id: 'handwriting', name: '手写混剪', description: '手写/文案类视频，金色配色' },
  { id: 'emotional', name: '情感混剪', description: '情感/励志类视频，粉紫配色' },
  { id: 'health', name: '养生混剪', description: '养生/健康类视频，暖色配色' },
]

onMounted(() => {
  const strats = props.globalConfig?.strategies || {}
  for (const s of strategyList) {
    local[s.id] = { ...(strats[s.id] || getDefaults(s.id)) }
  }
})

function getDefaults(id) {
  const map = {
    handwriting: { sticker_count: 14, sparkle_count: 5, sparkle_style: 'gold', color_scheme: 'random', enable_particles: true, enable_decorations: true, enable_border: true, enable_color_preset: true, enable_audio_fx: true },
    emotional: { sticker_count: 20, sparkle_count: 5, sparkle_style: 'pink', color_scheme: 'random', enable_particles: true, enable_decorations: true, enable_border: true, enable_color_preset: true, enable_audio_fx: true },
    health: { sticker_count: 20, sparkle_count: 5, sparkle_style: 'warm', color_scheme: 'random', enable_particles: true, enable_decorations: true, enable_border: true, enable_color_preset: true, enable_audio_fx: true },
  }
  return map[id] || map.handwriting
}

function getVal(sid, key) {
  return local[sid]?.[key] ?? getDefaults(sid)[key]
}

function setVal(sid, key, val) {
  if (!local[sid]) local[sid] = { ...getDefaults(sid) }
  local[sid] = { ...local[sid], [key]: val }
}

function toggleExpand(id) {
  const s = new Set(expanded.value)
  if (s.has(id)) { s.delete(id) } else { s.add(id) }
  expanded.value = s
}

function resetToDefaults(sid) {
  local[sid] = { ...getDefaults(sid) }
  saveStatus[sid] = '已恢复推荐设置'
  setTimeout(() => { saveStatus[sid] = '' }, 2000)
}

async function save(sid) {
  try {
    const cfg = props.globalConfig || {}
    if (!cfg.strategies) cfg.strategies = {}
    cfg.strategies[sid] = { ...local[sid] }
    await fetch('/api/config', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(cfg),
    })
    saveStatus[sid] = '已保存'
    emit('saved', cfg)
    setTimeout(() => { saveStatus[sid] = '' }, 2000)
  } catch (e) {
    saveStatus[sid] = '保存失败'
    setTimeout(() => { saveStatus[sid] = '' }, 3000)
  }
}
</script>
