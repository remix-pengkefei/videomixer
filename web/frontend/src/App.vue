<template>
  <div class="app">
    <!-- Phase 1: Environment Check -->
    <EnvCheck
      v-if="phase === 'env-check'"
      @ready="phase = 'main'"
    />

    <!-- Phase 2: Main UI with Sidebar -->
    <template v-else>
      <Sidebar
        :active-platform="activePlatform"
        :update-info="updateInfo"
        @select-platform="activePlatform = $event"
        @show-update="showUpdateDialog"
      />

      <div class="main-area">
        <AppHeader :current-tab="currentTab" @change-tab="currentTab = $event" />

        <main class="main-content">
          <!-- ===== Tab: Processing ===== -->
          <template v-if="currentTab === 'processing'">

            <!-- === Active Task View === -->
            <template v-if="taskId">
              <ProgressPanel
                :status="taskStatus"
                :completed="completed"
                :failed="failed"
                :total="total"
                :current-file="currentFile"
                :file-results="fileResults"
                :all-files="allFiles"
                :elapsed="elapsed"
                :log-lines="logLines"
                @cancel="cancelTask"
                @reset="resetTask"
                @open-folder="openOutputDir"
              />
            </template>

            <!-- === Setup View (no active task) === -->
            <template v-else>
              <!-- I/O Directories -->
              <div class="io-card">
                <div class="io-row">
                  <div class="io-label">输入目录</div>
                  <FolderPicker
                    compact
                    :path="inputDir"
                    placeholder="选择包含视频的文件夹"
                    @select="onSelectInput"
                  />
                </div>
                <div class="io-divider"></div>
                <div class="io-row">
                  <div class="io-label">输出目录</div>
                  <FolderPicker
                    compact
                    :path="outputDir"
                    placeholder="选择混剪结果保存位置"
                    @select="onSelectOutput"
                  />
                </div>
              </div>

              <!-- Category Summary -->
              <div v-if="categories.length > 0" class="category-summary-bar">
                <span class="check-icon">&#10003;</span>
                已识别 <strong>{{ categories.length }}</strong> 个分类，共 <strong>{{ totalVideos }}</strong> 个视频
              </div>

              <div v-else-if="inputDir" class="empty-notice">
                未检测到视频文件
              </div>

              <!-- Category Cards -->
              <CategoryList
                v-if="categories.length > 0"
                :categories="categories"
                :strategies="strategies"
                :configs="categoryConfigs"
                :task-active="false"
                @update-strategy="onUpdateStrategy"
                @update-config="onUpdateConfig"
              />

              <!-- Start Button -->
              <div v-if="categories.length > 0" class="action-row">
                <button
                  class="btn-start"
                  :disabled="!canStart"
                  @click="startTask"
                >
                  开始处理
                </button>
              </div>
            </template>
          </template>

          <!-- ===== Tab: Strategies ===== -->
          <StrategyConfig
            v-else-if="currentTab === 'strategies'"
            :strategies="strategies"
            :global-config="globalConfig"
            @saved="onGlobalConfigSaved"
          />

          <!-- ===== Tab: Asset Library ===== -->
          <AssetLibrary v-else-if="currentTab === 'assets'" />

          <!-- ===== Tab: History ===== -->
          <HistoryPanel v-else-if="currentTab === 'history'" />
        </main>
      </div>

      <!-- Update Dialog -->
      <div v-if="showUpdate" class="modal-overlay" @click.self="showUpdate = false">
        <div class="modal" style="max-width: 420px;">
          <div class="modal-header">
            <span class="modal-title">发现新版本</span>
            <button class="modal-close" @click="showUpdate = false">&times;</button>
          </div>
          <div class="modal-body" style="padding: 20px 24px;">
            <p style="font-size: 14px; color: var(--text-secondary); margin-bottom: 12px;">
              GitHub 仓库有 <strong>{{ updateInfo?.ahead }}</strong> 个新提交
            </p>
            <div v-if="updateInfo?.commits?.length" class="update-commits">
              <div
                v-for="c in updateInfo.commits"
                :key="c.sha"
                class="update-commit"
              >
                <span class="update-commit-sha">{{ c.sha.slice(0, 7) }}</span>
                <span class="update-commit-msg">{{ c.message }}</span>
              </div>
            </div>
            <p style="font-size: 13px; color: var(--text-tertiary); margin-top: 12px;">
              运行 <code style="background: var(--bg-subtle); padding: 2px 6px; border-radius: 4px;">git pull</code> 更新代码
            </p>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import Sidebar from './components/Sidebar.vue'
import AppHeader from './components/Header.vue'
import FolderPicker from './components/FolderPicker.vue'
import CategoryList from './components/CategoryList.vue'
import ProgressPanel from './components/ProgressPanel.vue'
import EnvCheck from './components/EnvCheck.vue'
import AssetLibrary from './components/AssetLibrary.vue'
import StrategyConfig from './components/StrategyConfig.vue'
import HistoryPanel from './components/HistoryPanel.vue'

const phase = ref('env-check')
const currentTab = ref('processing')
const activePlatform = ref('weixin')
const updateInfo = ref(null)
const showUpdate = ref(false)

const inputDir = ref('')
const outputDir = ref('')
const categories = ref([])
const strategies = ref([])
const categoryConfigs = reactive({})
const manuallyEdited = reactive({})
const globalConfig = ref({})

const taskId = ref(null)
const taskStatus = ref('')
const completed = ref(0)
const failed = ref(0)
const total = ref(0)
const currentFile = ref('')
const fileResults = ref([])
const elapsed = ref(0)
const logLines = ref([])
const allFiles = ref([])

let ws = null

const canStart = computed(() => {
  return inputDir.value && outputDir.value && categories.value.length > 0 && !taskId.value
})

const totalVideos = computed(() => {
  return categories.value.reduce((sum, c) => sum + c.video_count, 0)
})

function getDefaultConfig(strategy) {
  const globalStrats = globalConfig.value?.strategies || {}
  const g = globalStrats[strategy]
  if (g) {
    return {
      sticker_count: g.sticker_count ?? 14,
      sparkle_count: g.sparkle_count ?? 5,
      sparkle_style: g.sparkle_style ?? 'gold',
      color_scheme: g.color_scheme ?? 'random',
      enable_particles: g.enable_particles ?? true,
      enable_decorations: g.enable_decorations ?? true,
      enable_border: g.enable_border ?? true,
      enable_color_preset: g.enable_color_preset ?? true,
      enable_audio_fx: g.enable_audio_fx ?? true,
    }
  }
  const STRATEGY_DEFAULTS = {
    handwriting: { sticker_count: 14, sparkle_count: 5, sparkle_style: 'gold' },
    emotional:   { sticker_count: 20, sparkle_count: 5, sparkle_style: 'pink' },
    health:      { sticker_count: 20, sparkle_count: 5, sparkle_style: 'warm' },
  }
  const d = STRATEGY_DEFAULTS[strategy] || STRATEGY_DEFAULTS.handwriting
  return {
    sticker_count: d.sticker_count,
    sparkle_count: d.sparkle_count,
    sparkle_style: d.sparkle_style,
    color_scheme: 'random',
    enable_particles: true,
    enable_decorations: true,
    enable_border: true,
    enable_color_preset: true,
    enable_audio_fx: true,
  }
}

function initConfigs() {
  for (const cat of categories.value) {
    categoryConfigs[cat.folder] = getDefaultConfig(cat.strategy)
    manuallyEdited[cat.folder] = new Set()
  }
}

function showUpdateDialog() {
  showUpdate.value = true
}

// Load global config, strategies, and check for updates on startup
onMounted(async () => {
  try {
    const [cfgRes, stratRes] = await Promise.all([
      fetch('/api/config'),
      fetch('/api/strategies'),
    ])
    const cfg = await cfgRes.json()
    globalConfig.value = cfg

    if (cfg.last_input_dir) inputDir.value = cfg.last_input_dir
    if (cfg.last_output_dir) outputDir.value = cfg.last_output_dir

    if (cfg.last_input_dir) {
      try {
        const scanRes = await fetch(`/api/scan?path=${encodeURIComponent(cfg.last_input_dir)}`)
        const scanData = await scanRes.json()
        categories.value = scanData.categories
        initConfigs()
      } catch (e) {}
    }

    const stratData = await stratRes.json()
    strategies.value = stratData.strategies || stratData
  } catch (e) {
    try {
      const res = await fetch('/api/strategies')
      const data = await res.json()
      strategies.value = data.strategies || data
    } catch (_) {}
  }

  // Check for updates (non-blocking)
  try {
    const res = await fetch('/api/check-update')
    const data = await res.json()
    if (data.has_update) {
      updateInfo.value = data
    }
  } catch (e) {}
})

async function onSelectInput(path) {
  inputDir.value = path
  const res = await fetch(`/api/scan?path=${encodeURIComponent(path)}`)
  const data = await res.json()
  categories.value = data.categories
  initConfigs()
}

function onSelectOutput(path) {
  outputDir.value = path
}

function onUpdateStrategy(folder, strategy) {
  const cat = categories.value.find(c => c.folder === folder)
  if (cat) {
    cat.strategy = strategy
    const newDefaults = getDefaultConfig(strategy)
    const edited = manuallyEdited[folder] || new Set()
    const current = categoryConfigs[folder] || {}
    for (const [key, val] of Object.entries(newDefaults)) {
      if (!edited.has(key)) {
        current[key] = val
      }
    }
    categoryConfigs[folder] = { ...current }
  }
}

function onUpdateConfig(folder, key, value) {
  if (!categoryConfigs[folder]) return
  categoryConfigs[folder] = { ...categoryConfigs[folder], [key]: value }
  if (!manuallyEdited[folder]) manuallyEdited[folder] = new Set()
  manuallyEdited[folder].add(key)
}

function onGlobalConfigSaved(cfg) {
  globalConfig.value = { ...cfg }
}

async function startTask() {
  const body = {
    input_dir: inputDir.value,
    output_dir: outputDir.value,
    categories: categories.value.map(c => ({
      folder: c.folder,
      strategy: c.strategy,
      config: categoryConfigs[c.folder] || null,
    })),
  }

  const res = await fetch('/api/tasks', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  // Build flat file list for progress display
  const files = []
  for (const c of categories.value) {
    for (const f of (c.files || [])) {
      files.push({
        displayName: `${c.folder}/${f}`,
        filename: f,
        folder: c.folder,
        strategy: c.strategy,
      })
    }
  }
  allFiles.value = files

  const data = await res.json()
  taskId.value = data.task_id
  total.value = data.total
  taskStatus.value = 'running'
  completed.value = 0
  failed.value = 0
  fileResults.value = []
  currentFile.value = ''
  logLines.value = []

  connectWs(data.task_id)
}

function connectWs(id) {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  ws = new WebSocket(`${protocol}://${location.host}/ws/progress/${id}`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)

    if (msg.type === 'file_start') {
      currentFile.value = msg.filename
      completed.value = msg.completed
      failed.value = msg.failed
      logLines.value = []
    } else if (msg.type === 'file_log') {
      logLines.value = [...logLines.value, msg.line]
      if (logLines.value.length > 200) {
        logLines.value = logLines.value.slice(-150)
      }
    } else if (msg.type === 'file_done') {
      completed.value = msg.completed
      failed.value = msg.failed
      fileResults.value = [...fileResults.value, msg.result]
    } else if (msg.type === 'finished') {
      taskStatus.value = msg.status
      completed.value = msg.completed
      failed.value = msg.failed
      elapsed.value = msg.elapsed
      currentFile.value = ''
    } else if (msg.type === 'cancelled') {
      taskStatus.value = 'cancelled'
      currentFile.value = ''
    } else if (msg.type === 'state') {
      taskStatus.value = msg.status
      completed.value = msg.completed
      failed.value = msg.failed
      fileResults.value = msg.file_results || []
      currentFile.value = msg.current_file
    }
  }

  ws.onclose = () => {
    if (taskStatus.value === 'running') {
      setTimeout(() => connectWs(id), 2000)
    }
  }
}

async function cancelTask() {
  if (!taskId.value) return
  await fetch(`/api/tasks/${taskId.value}/cancel`, { method: 'POST' })
}

async function openOutputDir() {
  if (!outputDir.value) return
  await fetch('/api/open-folder', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: outputDir.value }),
  })
}

function resetTask() {
  taskId.value = null
  taskStatus.value = ''
  completed.value = 0
  failed.value = 0
  total.value = 0
  currentFile.value = ''
  fileResults.value = []
  allFiles.value = []
  elapsed.value = 0
  logLines.value = []
}

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>
