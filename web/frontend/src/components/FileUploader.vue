<template>
  <div class="uploader">
    <!-- Drop zone: click = pick folder -->
    <div
      :class="['drop-zone', { active: dragOver }]"
      @dragover.prevent="dragOver = true"
      @dragleave="dragOver = false"
      @drop.prevent="handleDrop"
      @click="pickFolder"
    >
      <svg width="40" height="40" viewBox="0 0 40 40" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.3">
        <rect x="4" y="8" width="32" height="24" rx="3"/>
        <path d="M20 14v12M14 20h12"/>
      </svg>
      <div class="drop-zone-text">点击选择文件夹上传</div>
      <div class="drop-zone-hint">支持 mp4, mov, mkv, avi 等格式 · 也可直接拖拽到此处</div>
      <a class="drop-zone-file-link" @click.stop="pickFiles">选择单个视频文件上传</a>
    </div>

    <!-- Upload progress -->
    <div v-if="uploadQueue.length > 0" class="upload-progress-list">
      <div v-for="item in uploadQueue" :key="item.id" class="upload-progress-item">
        <span class="upload-fname">{{ item.name }}</span>
        <div class="upload-progress-bar">
          <div
            class="upload-progress-fill"
            :class="{ done: item.progress >= 100 }"
            :style="{ width: item.progress + '%' }"
          ></div>
        </div>
        <span class="upload-pct">{{ Math.round(item.progress) }}%</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'

const props = defineProps({
  sessionId: { type: String, required: true },
})

const emit = defineEmits(['categoriesChanged'])

const dragOver = ref(false)
const uploadQueue = ref([])
const defaultCategory = '默认'

const VIDEO_EXTS = ['mp4', 'mov', 'm4v', 'avi', 'mkv', 'webm', 'flv', 'wmv']

function isVideo(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  return VIDEO_EXTS.includes(ext)
}

// --- Pick folder (click drop zone) ---
async function pickFolder() {
  try {
    const dirHandle = await window.showDirectoryPicker()
    const files = []
    for await (const entry of dirHandle.values()) {
      if (entry.kind === 'file') {
        const file = await entry.getFile()
        if (isVideo(file.name)) files.push(file)
      }
    }
    if (files.length > 0) {
      await doUpload(files, dirHandle.name)
    }
  } catch (e) {
    // User cancelled
  }
}

// --- Pick files (click link) ---
async function pickFiles() {
  try {
    const handles = await window.showOpenFilePicker({
      multiple: true,
      types: [{
        description: '视频文件',
        accept: { 'video/*': VIDEO_EXTS.map(e => '.' + e) },
      }],
    })
    const files = []
    for (const h of handles) {
      const file = await h.getFile()
      if (isVideo(file.name)) files.push(file)
    }
    if (files.length > 0) {
      await doUpload(files, defaultCategory)
    }
  } catch (e) {
    // User cancelled
  }
}

// --- Drag & Drop ---
async function handleDrop(event) {
  dragOver.value = false
  const items = event.dataTransfer?.items
  if (!items) return

  const entries = []
  for (const item of items) {
    const entry = item.webkitGetAsEntry?.()
    if (entry) entries.push(entry)
  }

  if (entries.length > 0) {
    for (const entry of entries) {
      if (entry.isDirectory) {
        const files = await readDirectoryFiles(entry)
        if (files.length > 0) await doUpload(files, entry.name)
      } else if (entry.isFile) {
        const file = await getFileFromEntry(entry)
        if (file && isVideo(file.name)) {
          await doUpload([file], defaultCategory)
        }
      }
    }
  } else {
    const files = Array.from(event.dataTransfer.files || []).filter(f => isVideo(f.name))
    if (files.length > 0) await doUpload(files, defaultCategory)
  }
}

// --- Upload logic ---
async function doUpload(files, category) {
  const safeCat = category.replace(/[/\\]/g, '_').trim() || defaultCategory

  for (const file of files) {
    const queueItem = reactive({
      id: Date.now() + Math.random(),
      name: file.name,
      progress: 0,
    })
    uploadQueue.value.push(queueItem)

    try {
      await uploadSingleFile(file, safeCat, queueItem)
    } catch (err) {
      console.error('Upload failed:', file.name, err)
    }

    setTimeout(() => {
      const idx = uploadQueue.value.indexOf(queueItem)
      if (idx >= 0) uploadQueue.value.splice(idx, 1)
    }, 800)
  }

  emit('categoriesChanged')
}

function uploadSingleFile(file, category, queueItem) {
  return new Promise((resolve, reject) => {
    const formData = new FormData()
    formData.append('session_id', props.sessionId)
    formData.append('category', category)
    formData.append('files', file)

    const xhr = new XMLHttpRequest()
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) {
        queueItem.progress = (e.loaded / e.total) * 100
      }
    }
    xhr.onload = () => {
      queueItem.progress = 100
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(JSON.parse(xhr.responseText))
      } else {
        reject(new Error(`HTTP ${xhr.status}`))
      }
    }
    xhr.onerror = () => reject(new Error('Network error'))
    xhr.open('POST', '/api/upload')
    xhr.send(formData)
  })
}

// --- Helpers for drag-drop directory reading ---
async function readDirectoryFiles(dirEntry) {
  return new Promise((resolve) => {
    const reader = dirEntry.createReader()
    const result = []
    function readBatch() {
      reader.readEntries(async (entries) => {
        if (entries.length === 0) { resolve(result); return }
        for (const entry of entries) {
          if (entry.isFile) {
            const file = await getFileFromEntry(entry)
            if (file && isVideo(file.name)) result.push(file)
          }
        }
        readBatch()
      })
    }
    readBatch()
  })
}

function getFileFromEntry(entry) {
  return new Promise((resolve) => {
    entry.file(resolve, () => resolve(null))
  })
}
</script>
