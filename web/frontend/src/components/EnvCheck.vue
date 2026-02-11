<template>
  <div class="env-check">
    <div class="env-check-card">
      <div class="env-check-header">
        <h1 class="env-check-title">VideoMixer</h1>
        <p class="env-check-subtitle">检查运行环境</p>
      </div>

      <div class="env-check-items">
        <div
          v-for="item in checkItems"
          :key="item.key"
          class="env-check-item"
        >
          <span class="env-check-icon" :class="item.status">
            <span v-if="item.status === 'checking'" class="spinner"></span>
            <svg v-else-if="item.status === 'ok'" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else-if="item.status === 'missing'" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M4 4L12 12M12 4L4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span v-else class="spinner" style="opacity:0.3"></span>
          </span>
          <div class="env-check-label">
            <span class="env-check-name">{{ item.name }}</span>
            <span class="env-check-detail">{{ item.detail }}</span>
          </div>
        </div>

        <div v-if="installing" class="env-install-section">
          <div class="env-install-label">正在安装 ffmpeg...</div>
          <div ref="terminalRef" class="env-install-output">
            <div
              v-for="(line, i) in installOutput"
              :key="i"
              class="env-install-line"
            >{{ line }}</div>
          </div>
        </div>
      </div>

      <div class="env-check-footer">
        <template v-if="allReady">
          <p class="env-check-ready">环境就绪</p>
          <button class="btn-continue" @click="$emit('ready')">
            继续
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M6 3L11 8L6 13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </template>
        <template v-else-if="hasMissing && !installing">
          <button
            v-if="ffmpegMissing"
            class="btn-install"
            @click="installFfmpeg"
          >
            安装 ffmpeg
          </button>
          <p v-if="assetsMissing && !ffmpegMissing" class="env-check-error">
            缺少素材文件，请检查 assets 目录
          </p>
        </template>
        <template v-else-if="!hasMissing && !allReady">
          <p class="env-check-status">正在检查...</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'

const emit = defineEmits(['ready'])

const checks = reactive({
  ffmpeg:   { status: 'pending', name: 'ffmpeg',   detail: '' },
  ffprobe:  { status: 'pending', name: 'ffprobe',  detail: '' },
  stickers: { status: 'pending', name: '贴纸素材', detail: '' },
  sparkles: { status: 'pending', name: '闪光素材', detail: '' },
})

const installing = ref(false)
const installOutput = ref([])
const terminalRef = ref(null)

const checkItems = computed(() =>
  Object.entries(checks).map(([key, val]) => ({ key, ...val }))
)

const allReady = computed(() =>
  Object.values(checks).every(c => c.status === 'ok')
)

const hasMissing = computed(() =>
  Object.values(checks).some(c => c.status === 'missing')
)

const ffmpegMissing = computed(() =>
  checks.ffmpeg.status === 'missing' || checks.ffprobe.status === 'missing'
)

const assetsMissing = computed(() =>
  checks.stickers.status === 'missing' || checks.sparkles.status === 'missing'
)

watch(installOutput, async () => {
  await nextTick()
  if (terminalRef.value) {
    terminalRef.value.scrollTop = terminalRef.value.scrollHeight
  }
}, { deep: true })

async function runCheck() {
  for (const c of Object.values(checks)) c.status = 'checking'

  try {
    const res = await fetch('/api/env-check')
    const data = await res.json()

    checks.ffmpeg.status = data.ffmpeg.installed ? 'ok' : 'missing'
    checks.ffmpeg.detail = data.ffmpeg.installed
      ? `v${data.ffmpeg.version}`
      : '未安装'

    checks.ffprobe.status = data.ffprobe.installed ? 'ok' : 'missing'
    checks.ffprobe.detail = data.ffprobe.installed
      ? data.ffprobe.path
      : '未安装'

    checks.stickers.status = (data.assets.stickers.exists && data.assets.stickers.count > 0) ? 'ok' : 'missing'
    checks.stickers.detail = data.assets.stickers.count > 0
      ? `${data.assets.stickers.count.toLocaleString()} 个`
      : '未找到'

    checks.sparkles.status = (data.assets.sparkles.exists && data.assets.sparkles.count > 0) ? 'ok' : 'missing'
    checks.sparkles.detail = data.assets.sparkles.count > 0
      ? `${data.assets.sparkles.count.toLocaleString()} 个`
      : '未找到'
  } catch {
    for (const c of Object.values(checks)) {
      if (c.status === 'checking') {
        c.status = 'missing'
        c.detail = '检查失败'
      }
    }
  }
}

function installFfmpeg() {
  installing.value = true
  installOutput.value = []

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${location.host}/ws/env-install`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'output') {
      installOutput.value.push(msg.line)
      if (installOutput.value.length > 300) {
        installOutput.value = installOutput.value.slice(-300)
      }
    } else if (msg.type === 'done') {
      installing.value = false
      if (msg.success) {
        runCheck()
      } else {
        installOutput.value.push(`\n错误: ${msg.error}`)
      }
    }
  }

  ws.onerror = () => {
    installing.value = false
    installOutput.value.push('连接失败')
  }
}

onMounted(() => {
  runCheck()
})
</script>
