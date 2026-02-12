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
        @select-platform="activePlatform = $event"
      />

      <div class="main-area">
        <AppHeader :current-tab="currentTab" :update-info="updateInfo" @change-tab="currentTab = $event" @update-checked="onUpdateChecked" @update-done="updateInfo = null" />

        <main class="main-content">
          <!-- ===== Tab: Processing ===== -->
          <div v-show="currentTab === 'processing'" class="tab-panel">
            <ProgressPanel
              v-if="taskId"
              :status="taskStatus"
              :completed="completed"
              :failed="failed"
              :total="total"
              :current-file="currentFile"
              :file-results="fileResults"
              :all-files="allFiles"
              :elapsed="elapsed"
              :log-lines="logLines"
              :task-id="taskId"
              @cancel="cancelTask"
              @download-all="downloadAll"
              @reset="resetTask"
            />
            <div v-else>
              <FileUploader
                :session-id="sessionId"
                @categories-changed="onCategoriesChanged"
              />
              <VideoList
                v-if="categories.length > 0"
                :categories="categories"
                :strategies="strategies"
                :strategy-presets="strategyPresets"
                :mixing-modes="mixingModes"
                :outputs="globalOutputs"
                @update-outputs="globalOutputs = $event"
                @start="startTask"
              />
            </div>
          </div>

          <!-- ===== Tab: Strategies ===== -->
          <div v-show="currentTab === 'strategies'" class="tab-panel">
            <StrategyConfig
              :strategies="strategies"
              :global-config="globalConfig"
              @saved="onGlobalConfigSaved"
            />
          </div>

          <!-- ===== Tab: Asset Library ===== -->
          <div v-show="currentTab === 'assets'" class="tab-panel">
            <AssetLibrary />
          </div>

          <!-- ===== Tab: Data Tracking ===== -->
          <div v-show="currentTab === 'data'" class="tab-panel">
            <DataPanel :platform="activePlatform" />
          </div>

          <!-- ===== Tab: History ===== -->
          <div v-show="currentTab === 'history'" class="tab-panel">
            <HistoryPanel />
          </div>
        </main>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import Sidebar from './components/Sidebar.vue'
import AppHeader from './components/Header.vue'
import FileUploader from './components/FileUploader.vue'
import VideoList from './components/VideoList.vue'
import ProgressPanel from './components/ProgressPanel.vue'
import EnvCheck from './components/EnvCheck.vue'
import AssetLibrary from './components/AssetLibrary.vue'
import StrategyConfig from './components/StrategyConfig.vue'
import DataPanel from './components/DataPanel.vue'
import HistoryPanel from './components/HistoryPanel.vue'

const phase = ref('env-check')
const currentTab = ref('processing')
const activePlatform = ref('weixin')
const updateInfo = ref(null)

// Session ID for upload workspace (fresh each page load)
const sessionId = ref(crypto.randomUUID().slice(0, 12))

const categories = ref([])
const strategies = ref([])
const strategyPresets = ref([])
const mixingModes = ref([])
const globalConfig = ref({})

// Global output config: each entry = { mode, preset }
const globalOutputs = ref([{ mode: 'standard', preset: 'D' }])

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

// Load global config and strategies on startup
onMounted(async () => {
  try {
    const [cfgRes, stratRes] = await Promise.all([
      fetch('/api/config'),
      fetch('/api/strategies'),
    ])
    const cfg = await cfgRes.json()
    globalConfig.value = cfg

    const stratData = await stratRes.json()
    strategies.value = stratData.strategies || stratData
    strategyPresets.value = stratData.strategy_presets || []
    mixingModes.value = stratData.mixing_modes || []
  } catch (e) {
    try {
      const res = await fetch('/api/strategies')
      const data = await res.json()
      strategies.value = data.strategies || data
      strategyPresets.value = data.strategy_presets || []
      mixingModes.value = data.mixing_modes || []
    } catch (_) {}
  }
})

// Check for updates only AFTER entering main UI
watch(phase, (val) => {
  if (val === 'main') {
    fetch('/api/check-update')
      .then(r => r.json())
      .then(data => {
        if (data.has_update) {
          updateInfo.value = data
        }
      })
      .catch(() => {})
  }
})

async function onCategoriesChanged() {
  const res = await fetch(`/api/upload/${sessionId.value}/scan`)
  const data = await res.json()
  categories.value = data.categories || []
}

function onGlobalConfigSaved(cfg) {
  globalConfig.value = { ...cfg }
}

function onUpdateChecked(data) {
  if (data.has_update) {
    updateInfo.value = data
  }
}

async function startTask() {
  const outputs = globalOutputs.value
  // All files share the same global outputs
  const body = {
    session_id: sessionId.value,
    categories: categories.value.map(c => {
      const fileList = (c.files || []).map(f => ({
        filename: f,
        outputs: outputs.map(o => ({ mode: o.mode, strategy_preset: o.preset })),
      }))
      return {
        folder: c.folder,
        strategy: c.strategy,
        config: null,
        files: fileList,
      }
    }),
  }

  const res = await fetch('/api/tasks/upload', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })

  // Build flat file list for progress display
  const count = outputs.length
  const files = []
  for (const c of categories.value) {
    for (const f of (c.files || [])) {
      for (let i = 0; i < count; i++) {
        const displayName = `${c.folder}/${f}` + (count > 1 ? ` #${i+1}` : '')
        files.push({
          displayName,
          filename: f,
          folder: c.folder,
          strategy: c.strategy,
        })
      }
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
      registerVideoStats()
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

async function registerVideoStats() {
  const now = new Date().toISOString()
  const videos = fileResults.value
    .filter(r => r.status === 'done')
    .map(r => ({
      id: r.video_id || `${taskId.value}_${r.filename}`,
      video_id: r.video_id || '',
      task_id: taskId.value,
      filename: r.filename,
      output_file: r.output_file || '',
      folder: r.folder || '',
      strategy: r.strategy || '',
      mode: r.mode || 'standard',
      strategy_preset: r.strategy_preset || 'D',
      platform: activePlatform.value,
      created_at: now,
      stats: {},
    }))
  if (videos.length > 0) {
    await fetch('/api/video-stats/batch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ videos }),
    }).catch(() => {})
  }
}

async function cancelTask() {
  if (!taskId.value) return
  await fetch(`/api/tasks/${taskId.value}/cancel`, { method: 'POST' })
}


function downloadAll() {
  if (!taskId.value) return
  window.open(`/api/download/${taskId.value}/all`, '_blank')
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
  // Reset session for fresh start
  sessionId.value = crypto.randomUUID().slice(0, 12)
  categories.value = []
  globalOutputs.value = [{ mode: 'standard', preset: 'D' }]
}

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>
