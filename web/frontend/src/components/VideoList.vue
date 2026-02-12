<template>
  <div class="vl">
    <!-- Summary bar -->
    <div class="vl-summary">
      <span class="vl-summary-icon">&#10003;</span>
      <span>已识别 <strong>{{ categoryCount }}</strong> 个分类，共 <strong>{{ videoCount }}</strong> 个视频</span>
    </div>

    <!-- Global output config (top) -->
    <div class="vl-config-card">
      <div class="vl-config-header">
        <span class="vl-config-title">生成份数</span>
        <input
          type="number"
          class="vl-count-input"
          :value="outputs.length"
          min="1"
          max="10"
          @change="onCountChange"
        />
        <span class="vl-config-total">共生成 <strong>{{ videoCount * outputs.length }}</strong> 个视频</span>
      </div>
      <div class="vl-output-rows">
        <div v-for="(out, i) in outputs" :key="i" class="vl-output-row">
          <span class="vl-output-label">第 {{ i + 1 }} 份</span>
          <div class="vl-output-field">
            <span class="vl-field-label">模式</span>
            <select class="vl-select" :value="out.mode" @change="onOutputChange(i, 'mode', $event.target.value)">
              <option v-for="m in mixingModes" :key="m.id" :value="m.id">{{ m.name }}</option>
            </select>
          </div>
          <div class="vl-output-field">
            <span class="vl-field-label">策略</span>
            <select class="vl-select" :value="out.preset" @change="onOutputChange(i, 'preset', $event.target.value)">
              <option v-for="p in strategyPresets" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Video table -->
    <div class="vl-table-wrap">
      <table class="vl-table">
        <thead>
          <tr>
            <th class="vl-th-cat">分类</th>
            <th>文件名</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in videos" :key="v.key" class="vl-row">
            <td class="vl-td-cat">
              <span class="strategy-tag-sm" :class="v.strategy">{{ strategyLabel(v.strategy) }}</span>
            </td>
            <td class="vl-td-name" :title="v.filename">{{ v.filename }}</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Start button -->
    <div class="vl-action">
      <button class="btn-start" @click="$emit('start')">开始处理</button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  categories: { type: Array, default: () => [] },
  strategies: { type: Array, default: () => [] },
  strategyPresets: { type: Array, default: () => [] },
  mixingModes: { type: Array, default: () => [] },
  outputs: { type: Array, default: () => [{ mode: 'standard', preset: 'D' }] },
})

const emit = defineEmits(['start', 'update-outputs'])

const strategyLabelMap = { handwriting: '手写', emotional: '情感', health: '养生', none: '无分类' }
function strategyLabel(id) {
  return strategyLabelMap[id] || id
}

const PRESET_ORDER = ['D', 'C', 'B', 'E', 'A']

const videos = computed(() => {
  const list = []
  for (const cat of props.categories) {
    for (const f of (cat.files || [])) {
      list.push({
        key: `${cat.folder}/${f}`,
        folder: cat.folder,
        strategy: cat.strategy,
        filename: f,
      })
    }
  }
  return list
})

const categoryCount = computed(() => props.categories.length)
const videoCount = computed(() => videos.value.length)

function onCountChange(event) {
  let val = parseInt(event.target.value) || 1
  val = Math.max(1, Math.min(10, val))
  event.target.value = val

  const current = [...props.outputs]
  if (val > current.length) {
    while (current.length < val) {
      const idx = current.length
      const preset = PRESET_ORDER[idx % PRESET_ORDER.length]
      current.push({ mode: 'standard', preset })
    }
  } else {
    current.length = val
  }
  emit('update-outputs', current)
}

function onOutputChange(index, field, value) {
  const updated = props.outputs.map((o, i) => {
    if (i === index) return { ...o, [field]: value }
    return { ...o }
  })
  emit('update-outputs', updated)
}
</script>
