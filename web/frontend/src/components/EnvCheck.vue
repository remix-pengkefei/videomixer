<template>
  <div class="env-splash">
    <div class="env-splash-inner">
      <!-- Brand -->
      <div class="env-brand">
        <div class="env-logo">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none">
            <rect width="56" height="56" rx="14" fill="url(#lg)"/>
            <path d="M20 16l18 12-18 12V16z" fill="#fff" opacity="0.95"/>
            <defs><linearGradient id="lg" x1="0" y1="0" x2="56" y2="56"><stop stop-color="#18181b"/><stop offset="1" stop-color="#3f3f46"/></linearGradient></defs>
          </svg>
        </div>
        <h1 class="env-title">VideoMixer</h1>
        <p class="env-version">v1.0</p>
      </div>

      <!-- Check items -->
      <div class="env-checks">
        <div
          v-for="item in checkItems"
          :key="item.key"
          class="env-row"
          :class="item.status"
        >
          <span class="env-row-icon">
            <span v-if="item.status === 'checking'" class="spinner"></span>
            <svg v-else-if="item.status === 'ok'" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="8" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
              <path d="M5.5 9.5L7.5 12L12.5 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else-if="item.status === 'missing'" width="18" height="18" viewBox="0 0 18 18" fill="none">
              <circle cx="9" cy="9" r="8" stroke="currentColor" stroke-width="1.5" opacity="0.3"/>
              <path d="M6.5 6.5l5 5M11.5 6.5l-5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
            <span v-else class="spinner" style="opacity:0.3"></span>
          </span>
          <span class="env-row-name">{{ item.name }}</span>
          <span class="env-row-desc">{{ item.desc }}</span>
          <span class="env-row-detail">{{ item.detail }}</span>
        </div>
      </div>

      <!-- Install output -->
      <div v-if="installing" class="env-install-section">
        <div class="env-install-label">正在安装 ffmpeg...</div>
        <div ref="terminalRef" class="env-install-output">
          <div v-for="(line, i) in installOutput" :key="i" class="env-install-line">{{ line }}</div>
        </div>
      </div>

      <!-- Actions -->
      <div class="env-actions">
        <button v-if="ffmpegMissing && !installing" class="env-btn-install" @click="installFfmpeg">安装 ffmpeg</button>
        <p v-if="assetsMissing && !ffmpegMissing && !installing" class="env-error-text">缺少素材文件，请检查 assets 目录</p>
        <button class="env-btn-go" :disabled="!allReady" @click="$emit('ready')">
          进入工作台
          <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
            <path d="M7 4l6 5-6 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick, watch } from 'vue'

const emit = defineEmits(['ready'])

const checks = reactive({
  ffmpeg:   { status: 'pending', name: 'ffmpeg',   desc: '视频编码引擎', detail: '' },
  ffprobe:  { status: 'pending', name: 'ffprobe',  desc: '视频信息探测', detail: '' },
  stickers: { status: 'pending', name: '贴纸素材', desc: '随机装饰贴纸', detail: '' },
  sparkles: { status: 'pending', name: '闪光素材', desc: '闪光粒子效果', detail: '' },
})

const installing = ref(false)
const installOutput = ref([])
const terminalRef = ref(null)

const checkItems = computed(() =>
  Object.entries(checks).map(([key, val]) => ({ key, ...val }))
)

const allChecks = computed(() => Object.values(checks))

const allReady = computed(() =>
  allChecks.value.every(c => c.status === 'ok')
)

const hasMissing = computed(() =>
  allChecks.value.some(c => c.status === 'missing')
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
  for (const c of Object.values(checks)) {
    c.status = 'checking'
    c.detail = ''
  }
  checks.ffmpeg.detail = '检测中...'
  checks.ffprobe.detail = '检测中...'
  checks.stickers.detail = '扫描目录...'
  checks.sparkles.detail = '扫描目录...'

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
