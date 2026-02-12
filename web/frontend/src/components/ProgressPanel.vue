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
          停止处理
        </button>
        <button v-if="isFinished && hasSuccessFiles" class="pp-btn-download" @click="$emit('download-all')">
          下载全部
        </button>
        <button v-if="isFinished" class="pp-btn-back" @click="$emit('reset')">
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

      <!-- Running: expandable file list -->
      <template v-if="!isFinished">
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
      </template>
    </div>

    <!-- 3. Running: Terminal -->
    <div v-if="!isFinished" class="term">
      <div class="term-chrome">
        <div class="term-dots">
          <span class="term-dot red"></span>
          <span class="term-dot yellow"></span>
          <span class="term-dot green"></span>
        </div>
        <div class="term-title">
          <template v-if="currentFile">{{ currentFile }}</template>
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

    <!-- 4. Finished: Result List -->
    <div v-if="isFinished" class="pp-results">
      <div class="pp-results-header">处理结果</div>
      <div class="pp-results-list">
        <div
          v-for="(vf, i) in videoList"
          :key="i"
          :class="['pp-result-row', vf.status]"
        >
          <span class="pp-result-icon">
            <template v-if="vf.status === 'done'">&#10003;</template>
            <template v-else-if="vf.status === 'failed'">&#10007;</template>
            <template v-else>&#9675;</template>
          </span>
          <span class="pp-result-name">{{ vf.displayName }}</span>
          <span v-if="vf.elapsed" class="pp-result-time">{{ Math.round(vf.elapsed) }}s</span>
          <span v-if="vf.status === 'failed' && vf.error" class="pp-result-error">{{ vf.error }}</span>
          <a
            v-if="vf.status === 'done' && vf.downloadUrl"
            class="pp-result-dl"
            :href="vf.downloadUrl"
            target="_blank"
          >下载</a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, watch, nextTick, onBeforeUnmount } from 'vue'

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
  taskId: String,
})

defineEmits(['cancel', 'download-all', 'reset'])

const termRef = ref(null)
const expanded = ref(false)

const isFinished = computed(() => {
  return props.status && props.status !== 'running'
})

const hasSuccessFiles = computed(() => {
  return (props.fileResults || []).some(r => r.status === 'done')
})

// --- Per-video progress parsing ---
const videoDuration = ref(0)
const currentTime = ref(0)

const videoPercent = computed(() => {
  if (props.status === 'completed' || props.status === 'failed' || props.status === 'cancelled') {
    return 100
  }
  if (!props.currentFile) return 0
  if (videoDuration.value > 0 && currentTime.value > 0) {
    return Math.min(99, Math.round((currentTime.value / videoDuration.value) * 100))
  }
  return 0
})

watch(() => props.logLines.length, () => {
  const lines = props.logLines
  if (lines.length === 0) return

  for (let i = Math.max(0, lines.length - 5); i < lines.length; i++) {
    const line = lines[i]

    if (!videoDuration.value) {
      const durMatch = line.match(/时长:\s*(\d+\.?\d*)秒/)
      if (durMatch) {
        videoDuration.value = parseFloat(durMatch[1])
      }
    }

    const timeMatch = line.match(/time=(\d+):(\d+):(\d+\.\d+)/)
    if (timeMatch) {
      const h = parseInt(timeMatch[1])
      const m = parseInt(timeMatch[2])
      const s = parseFloat(timeMatch[3])
      currentTime.value = h * 3600 + m * 60 + s
    }
  }
})

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
  const map = { running: '处理中', completed: '已完成', failed: '有失败', cancelled: '已停止' }
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
    let error = ''
    let downloadUrl = ''
    if (r) {
      status = r.status
      elapsed = r.elapsed
      error = r.error || ''
      if (r.status === 'done' && r.folder && r.output_file && props.taskId) {
        downloadUrl = `/api/download/${props.taskId}/${r.folder}/${r.output_file}`
      }
    } else if (props.currentFile === f.displayName) {
      status = 'running'
    }
    return { ...f, status, elapsed, error, downloadUrl }
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
