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
        <option v-for="s in strategies" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
    </div>

    <!-- Mode & Preset Row -->
    <div class="category-config-row">
      <div class="output-select-group">
        <label class="output-label">模式</label>
        <select
          class="output-select"
          :value="getMode(cat.folder)"
          :disabled="taskActive"
          @change="onChangeMode(cat.folder, $event.target.value)"
        >
          <option v-for="m in mixingModes" :key="m.id" :value="m.id">{{ m.name }}</option>
        </select>
      </div>
      <div class="output-select-group">
        <label class="output-label">策略</label>
        <select
          class="output-select"
          :value="getPreset(cat.folder)"
          :disabled="taskActive"
          @change="onChangePreset(cat.folder, $event.target.value)"
        >
          <option v-for="p in strategyPresets" :key="p.id" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
      <button class="btn-detail-config" @click="$emit('goStrategy')">详细配置</button>
    </div>

    <!-- Compact File List -->
    <div class="category-files">
      <div v-for="f in cat.files" :key="f" class="category-file-row">
        <span class="category-file-icon">&#9654;</span>
        <span class="category-file-name">{{ f }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  categories: Array,
  strategies: Array,
  strategyPresets: { type: Array, default: () => [] },
  mixingModes: { type: Array, default: () => [] },
  outputs: { type: Object, default: () => ({}) },
  taskActive: { type: Boolean, default: false },
})

const emit = defineEmits(['updateStrategy', 'updateOutputs', 'goStrategy'])

function strategyLabel(id) {
  const map = { handwriting: '手写', emotional: '情感', health: '养生' }
  return map[id] || id
}

function getMode(folder) {
  return props.outputs?.[folder]?.[0]?.mode || 'standard'
}

function getPreset(folder) {
  return props.outputs?.[folder]?.[0]?.strategy_preset || 'D'
}

function onChangeMode(folder, mode) {
  const preset = getPreset(folder)
  emit('updateOutputs', folder, [{ mode, strategy_preset: preset }])
}

function onChangePreset(folder, preset) {
  const mode = getMode(folder)
  emit('updateOutputs', folder, [{ mode, strategy_preset: preset }])
}
</script>
