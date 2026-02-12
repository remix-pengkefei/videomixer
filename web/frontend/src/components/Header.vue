<template>
  <header class="header">
    <div class="header-inner">
      <nav class="header-tabs">
        <button
          class="header-tab"
          :class="{ active: currentTab === 'processing' }"
          @click="$emit('changeTab', 'processing')"
        >
          混剪
        </button>
        <button
          class="header-tab"
          :class="{ active: currentTab === 'strategies' }"
          @click="$emit('changeTab', 'strategies')"
        >
          策略
        </button>
        <button
          class="header-tab"
          :class="{ active: currentTab === 'assets' }"
          @click="$emit('changeTab', 'assets')"
        >
          素材库
        </button>
        <button
          class="header-tab"
          :class="{ active: currentTab === 'data' }"
          @click="$emit('changeTab', 'data')"
        >
          视频管理
        </button>
        <button
          class="header-tab"
          :class="{ active: currentTab === 'history' }"
          @click="$emit('changeTab', 'history')"
        >
          操作记录
        </button>
      </nav>

      <!-- Right: Version / Update -->
      <div class="header-right">
        <!-- Has update -->
        <template v-if="updateInfo?.has_update && !updateDone">
          <div class="hdr-update-badge" @click="showPanel = !showPanel">
            <span class="hdr-update-dot"></span>
            <span>{{ updateInfo.ahead }} 个更新可用</span>
          </div>
        </template>

        <!-- Update done -->
        <template v-else-if="updateDone">
          <span class="hdr-version updated">已更新，请刷新页面</span>
        </template>

        <!-- No update -->
        <template v-else>
          <span class="hdr-version" @click="recheckUpdate">
            {{ checking ? '检查中...' : 'v1.0 · 暂无新版本' }}
          </span>
        </template>
      </div>
    </div>

    <!-- Update dropdown panel -->
    <div v-if="showPanel" class="hdr-update-panel">
      <div class="hdr-update-panel-header">
        <span class="hdr-update-panel-title">版本更新</span>
        <button class="hdr-update-panel-close" @click="showPanel = false">&times;</button>
      </div>

      <div class="hdr-update-panel-body">
        <p class="hdr-update-summary">
          GitHub 仓库有 <strong>{{ updateInfo?.ahead }}</strong> 个新提交
        </p>

        <div v-if="updateInfo?.commits?.length" class="hdr-update-commits">
          <div
            v-for="c in updateInfo.commits"
            :key="c.sha"
            class="hdr-update-commit"
          >
            <span class="hdr-commit-sha">{{ c.sha.slice(0, 7) }}</span>
            <span class="hdr-commit-msg">{{ c.message }}</span>
          </div>
        </div>

        <!-- Pull output -->
        <div v-if="pullOutput.length > 0" class="hdr-pull-output">
          <div v-for="(line, i) in pullOutput" :key="i" class="hdr-pull-line">{{ line }}</div>
        </div>

        <div class="hdr-update-panel-actions">
          <button
            v-if="!pulling && !updateDone"
            class="hdr-btn-pull"
            @click="runGitPull"
          >
            更新代码
          </button>
          <span v-if="pulling" class="hdr-pulling">
            <span class="mini-spinner"></span> 更新中...
          </span>
          <span v-if="updateDone && pullSuccess" class="hdr-pull-ok">更新成功，请刷新页面</span>
          <span v-if="updateDone && !pullSuccess" class="hdr-pull-fail">更新失败</span>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  currentTab: String,
  updateInfo: Object,
})

// emits defined above with recheckUpdate

const showPanel = ref(false)
const pulling = ref(false)
const pullOutput = ref([])
const updateDone = ref(false)
const pullSuccess = ref(false)
const checking = ref(false)

const emit = defineEmits(['changeTab', 'updateChecked', 'updateDone'])

function recheckUpdate() {
  if (checking.value) return
  checking.value = true
  fetch('/api/check-update')
    .then(r => r.json())
    .then(data => {
      checking.value = false
      emit('updateChecked', data)
    })
    .catch(() => { checking.value = false })
}

function runGitPull() {
  pulling.value = true
  pullOutput.value = []

  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  const ws = new WebSocket(`${protocol}://${location.host}/ws/git-pull`)

  ws.onmessage = (event) => {
    const msg = JSON.parse(event.data)
    if (msg.type === 'output') {
      pullOutput.value.push(msg.line)
    } else if (msg.type === 'done') {
      pulling.value = false
      updateDone.value = true
      pullSuccess.value = msg.success
      if (msg.success) {
        localStorage.removeItem('vm_update_info')
        emit('updateDone')
      }
      if (!msg.success && msg.error) {
        pullOutput.value.push(`错误: ${msg.error}`)
      }
    }
  }

  ws.onerror = () => {
    pulling.value = false
    updateDone.value = true
    pullSuccess.value = false
    pullOutput.value.push('连接失败')
  }
}

// Close panel when clicking outside
watch(showPanel, (val) => {
  if (val) {
    const handler = (e) => {
      const panel = document.querySelector('.hdr-update-panel')
      const badge = document.querySelector('.hdr-update-badge')
      if (panel && !panel.contains(e.target) && badge && !badge.contains(e.target)) {
        showPanel.value = false
        document.removeEventListener('click', handler)
      }
    }
    setTimeout(() => document.addEventListener('click', handler), 0)
  }
})
</script>
