<template>
  <div class="pp">
    <!-- 1. Stats Bar -->
    <div class="pp-stats-bar">
      <div class="pp-stats-left">
        <div class="pp-stat">
          <span class="pp-stat-num ok">{{ completed }}</span>
          <span class="pp-stat-label">成功</span>
        </div>
        <div class="pp-stat">
          <span class="pp-stat-num err">{{ failed }}</span>
          <span class="pp-stat-label">失败</span>
        </div>
        <div class="pp-stat">
          <span class="pp-stat-num">{{ formatTime(elapsed || localElapsed) }}</span>
          <span class="pp-stat-label">耗时</span>
        </div>
      </div>
      <div class="pp-stats-right">
        <button v-if="status === 'running'" class="pp-btn-cancel" @click="$emit('cancel')">
          取消
        </button>
        <button v-if="status && status !== 'running'" class="pp-btn-open" @click="$emit('openFolder')">
          打开目录
        </button>
        <button v-if="status && status !== 'running'" class="pp-btn-back" @click="$emit('reset')">
          返回
        </button>
      </div>
    </div>

    <!-- 2. Progress Section -->
    <div class="pp-progress-section">
      <!-- Current video row -->
      <div class="pp-current-row">
        <div class="pp-current-left">
          <span class="pp-badge" :class="status">{{ statusText }}</span>
          <span v-if="currentFile" class="pp-current-name">{{ currentFile }}</span>
          <span v-else-if="status === 'completed'" class="pp-current-name">全部完成</span>
          <span v-else-if="status === 'failed'" class="pp-current-name">处理结束</span>
        </div>
        <div class="pp-current-right">
          <span class="pp-current-count">{{ completed + failed }}/{{ total }}</span>
          <span class="pp-current-pct">{{ videoPercent }}%</span>
        </div>
      </div>

      <!-- Progress bar (per-video) -->
      <div class="pp-bar">
        <div
          class="pp-bar-fill"
          :class="{ done: status === 'completed', error: status === 'failed' }"
          :style="{ width: videoPercent + '%' }"
        ></div>
      </div>

      <!-- Expandable file list -->
      <div class="pp-file-toggle" @click="expanded = !expanded">
        <span class="pp-toggle-icon">{{ expanded ? '\u25B4' : '\u25BE' }}</span>
        <span>全部视频</span>
        <span class="pp-toggle-count">{{ completed + failed }}/{{ total }}</span>
      </div>

      <div v-if="expanded" class="pp-file-list">
        <div
          v-for="(vf, i) in videoList"
          :key="i"
          :class="['pp-frow', vf.status]"
        >
          <span class="pp-frow-icon">
            <template v-if="vf.status === 'done'">&#10003;</template>
            <template v-else-if="vf.status === 'failed'">&#10007;</template>
            <template v-else-if="vf.status === 'running'">
              <span class="mini-spinner"></span>
            </template>
            <template v-else>&#9675;</template>
          </span>
          <span class="pp-frow-name">{{ vf.displayName }}</span>
          <span v-if="vf.elapsed" class="pp-frow-time">{{ Math.round(vf.elapsed) }}s</span>
        </div>
      </div>
    </div>

    <!-- 3. Terminal -->
    <div class="term">
      <div class="term-chrome">
        <div class="term-dots">
          <span class="term-dot red"></span>
          <span class="term-dot yellow"></span>
          <span class="term-dot green"></span>
        </div>
        <div class="term-title">
          <template v-if="currentFile">{{ currentFile }}</template>
          <template v-else-if="status === 'completed'">Done</template>
          <template v-else-if="status === 'failed'">Error</template>
          <template v-else>VideoMixer</template>
        </div>
        <div class="term-dots" style="visibility:hidden">
          <span class="term-dot"></span>
          <span class="term-dot"></span>
          <span class="term-dot"></span>
        </div>
      </div>
      <div class="term-body" ref="termRef">
        <template v-if="logLines.length > 0">
          <div
            v-for="(line, i) in logLines"
            :key="i"
            class="term-line"
            :class="classifyLine(line)"
          >{{ line }}</div>
        </template>
        <div v-else-if="status === 'running'" class="term-line dim">
          Waiting for output...
        </div>
        <span v-if="status === 'running'" class="term-cursor"></span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  status: String,
  completed: Number,
  failed: Number,
  total: Number,
  currentFile: String,
  fileResults: Array,
  allFiles: { type: Array, default: () => [] },
  elapsed: Number,
  logLines: { type: Array, default: () => [] },
})

defineEmits(['cancel', 'reset', 'openFolder'])

const termRef = ref(null)
const expanded = ref(false)

// --- Per-video progress parsing ---
const videoDuration = ref(0)
const currentTime = ref(0)

const videoPercent = computed(() => {
  // Task finished — show 100%
  if (props.status === 'completed' || props.status === 'failed' || props.status === 'cancelled') {
    return 100
  }
  // No current file yet
  if (!props.currentFile) return 0
  // Parse-based percentage
  if (videoDuration.value > 0 && currentTime.value > 0) {
    return Math.min(99, Math.round((currentTime.value / videoDuration.value) * 100))
  }
  return 0
})

// Parse log lines for duration and ffmpeg time=
watch(() => props.logLines.length, () => {
  const lines = props.logLines
  if (lines.length === 0) return

  // Check latest lines (usually the new ones)
  for (let i = Math.max(0, lines.length - 5); i < lines.length; i++) {
    const line = lines[i]

    // Parse total duration: "时长: 30.5秒"
    if (!videoDuration.value) {
      const durMatch = line.match(/时长:\s*(\d+\.?\d*)秒/)
      if (durMatch) {
        videoDuration.value = parseFloat(durMatch[1])
      }
    }

    // Parse ffmpeg progress: "time=00:01:23.45"
    const timeMatch = line.match(/time=(\d+):(\d+):(\d+\.\d+)/)
    if (timeMatch) {
      const h = parseInt(timeMatch[1])
      const m = parseInt(timeMatch[2])
      const s = parseFloat(timeMatch[3])
      currentTime.value = h * 3600 + m * 60 + s
    }
  }
})

// Reset per-video progress when currentFile changes
watch(() => props.currentFile, () => {
  videoDuration.value = 0
  currentTime.value = 0
})

// --- Local elapsed timer ---
const localElapsed = ref(0)
let timerStart = 0
let timerId = null

watch(() => props.status, (s) => {
  if (s === 'running' && !timerId) {
    timerStart = Date.now()
    timerId = setInterval(() => {
      localElapsed.value = (Date.now() - timerStart) / 1000
    }, 1000)
  } else if (s !== 'running' && timerId) {
    clearInterval(timerId)
    timerId = null
  }
}, { immediate: true })

onBeforeUnmount(() => {
  if (timerId) clearInterval(timerId)
})

// --- Computed ---
const statusText = computed(() => {
  const map = { running: '处理中', completed: '已完成', failed: '有失败', cancelled: '已取消' }
  return map[props.status] || props.status
})

const videoList = computed(() => {
  const resultMap = {}
  for (const fr of (props.fileResults || [])) {
    resultMap[fr.filename] = fr
  }
  return props.allFiles.map(f => {
    const r = resultMap[f.displayName]
    let status = 'pending'
    let elapsed = null
    if (r) {
      status = r.status
      elapsed = r.elapsed
    } else if (props.currentFile === f.displayName) {
      status = 'running'
    }
    return { ...f, status, elapsed }
  })
})

// --- Helpers ---
function classifyLine(line) {
  if (/^frame=|^size=|fps=/.test(line)) return 'progress'
  if (/^={3,}/.test(line)) return 'header'
  if (/错误|Error|error|Invalid|failed/i.test(line)) return 'error'
  if (/完成|成功|Done/i.test(line)) return 'success'
  if (/输入:|输出:|时长:|贴纸:|配色:|遮罩:|边框:|装饰:|粒子:|调色:|音效:|闪光:/.test(line)) return 'info'
  if (/处理中|Processing/.test(line)) return 'dim'
  return ''
}

watch(() => props.logLines.length, async () => {
  await nextTick()
  if (termRef.value) {
    termRef.value.scrollTop = termRef.value.scrollHeight
  }
})

function formatTime(seconds) {
  if (!seconds) return '0s'
  if (seconds < 60) return Math.round(seconds) + 's'
  const m = Math.floor(seconds / 60)
  const s = Math.round(seconds % 60)
  return `${m}m${s}s`
}
</script>
