<template>
  <div class="history-page">
    <div class="history-page-header">
      <div>
        <h2 class="history-page-title">处理记录</h2>
        <p class="history-page-desc">查看历史混剪任务和处理结果</p>
      </div>
      <button
        v-if="tasks.length > 0"
        class="btn-clear-history"
        @click="clearHistory"
      >
        清空记录
      </button>
    </div>

    <div v-if="loading" class="history-loading">
      <div class="spinner"></div>
      <div>加载记录...</div>
    </div>

    <div v-else-if="tasks.length === 0" class="history-empty">
      暂无处理记录
    </div>

    <template v-else>
      <div
        v-for="task in tasks"
        :key="task.id"
        class="history-item"
      >
        <div class="history-item-header" @click="toggleExpand(task.id)">
          <div class="history-item-info">
            <div class="history-item-time">{{ formatTime(task.timestamp) }}</div>
            <div class="history-item-path">
              {{ shortenPath(task.input_dir) }}
            </div>
          </div>

          <div class="history-item-stats">
            <span class="history-stat ok">{{ task.completed }}</span>
            <span v-if="task.failed > 0" class="history-stat err">{{ task.failed }}</span>
            <span class="history-stat total">/ {{ task.total }}</span>
          </div>

          <div class="history-item-meta">
            <span :class="['history-badge', task.status]">
              {{ statusLabel(task.status) }}
            </span>
            <span class="history-elapsed">{{ formatElapsed(task.elapsed) }}</span>
          </div>

          <!-- Quick download button (no expand needed) -->
          <button
            v-if="task.completed > 0"
            class="history-dl-btn"
            title="下载全部"
            @click.stop="downloadAll(task.id)"
          >
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M7 2v8M4 7l3 3 3-3"/>
              <path d="M2 11h10"/>
            </svg>
          </button>

          <span class="history-expand-icon">
            {{ expandedIds.has(task.id) ? '▴' : '▾' }}
          </span>
        </div>

        <div v-if="expandedIds.has(task.id)" class="history-detail">
          <div class="history-detail-row">
            <span class="history-detail-label">输入</span>
            <span class="history-detail-value">{{ task.input_dir }}</span>
          </div>
          <div class="history-detail-row">
            <span class="history-detail-label">输出</span>
            <span class="history-detail-value">{{ task.output_dir }}</span>
          </div>
          <div class="history-detail-row">
            <span class="history-detail-label">分类</span>
            <span class="history-detail-value">
              <span
                v-for="c in task.categories"
                :key="c.folder"
                class="history-cat-tag"
              >
                {{ c.folder }} ({{ c.strategy }}, {{ c.count }}个)
              </span>
            </span>
          </div>

          <div v-if="task.file_results?.length" class="history-files">
            <div class="history-files-title">处理详情</div>
            <div
              v-for="(fr, i) in task.file_results"
              :key="i"
              :class="['history-file-row', fr.status]"
            >
              <span class="history-file-icon">
                {{ fr.status === 'done' ? '&#10003;' : '&#10007;' }}
              </span>
              <span class="history-file-name">{{ fr.filename }}</span>
              <span class="history-file-time">{{ fr.elapsed }}s</span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const loading = ref(true)
const tasks = ref([])
const expandedIds = ref(new Set())

onMounted(() => { loadHistory() })

async function loadHistory() {
  loading.value = true
  try {
    const res = await fetch('/api/history')
    const data = await res.json()
    tasks.value = data.tasks || []
  } catch (e) {
    console.error('Failed to load history:', e)
  } finally {
    loading.value = false
  }
}

async function clearHistory() {
  if (!confirm('确定要清空所有处理记录吗？')) return
  await fetch('/api/history', { method: 'DELETE' })
  tasks.value = []
}

function toggleExpand(id) {
  const s = new Set(expandedIds.value)
  if (s.has(id)) {
    s.delete(id)
  } else {
    s.add(id)
  }
  expandedIds.value = s
}

function downloadAll(taskId) {
  window.location.href = `/api/download/${taskId}/all`
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

function shortenPath(p) {
  if (!p) return ''
  const parts = p.split('/')
  if (parts.length > 3) {
    return '.../' + parts.slice(-2).join('/')
  }
  return p
}

function formatElapsed(sec) {
  if (!sec) return ''
  if (sec < 60) return `${sec}s`
  const m = Math.floor(sec / 60)
  const s = Math.round(sec % 60)
  return `${m}m${s}s`
}

function statusLabel(status) {
  const map = {
    completed: '完成',
    failed: '失败',
    cancelled: '取消',
    running: '进行中',
  }
  return map[status] || status
}
</script>
