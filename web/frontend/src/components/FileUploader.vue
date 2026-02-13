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

    <!-- Hidden fallback inputs for non-secure contexts (http://IP access) -->
    <input
      ref="folderInput"
      type="file"
      multiple
      webkitdirectory
      :accept="VIDEO_EXTS.map(e => '.' + e).join(',')"
      style="display:none"
      @change="onFolderInputChange"
    />
    <input
      ref="fileInput"
      type="file"
      multiple
      :accept="VIDEO_EXTS.map(e => '.' + e).join(',')"
      style="display:none"
      @change="onFileInputChange"
    />

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

const emit = defineEmits(['categoriesChanged', 'folderName'])

const dragOver = ref(false)
const uploadQueue = ref([])
const defaultCategory = '默认'
const folderInput = ref(null)
const fileInput = ref(null)

const VIDEO_EXTS = ['mp4', 'mov', 'm4v', 'avi', 'mkv', 'webm', 'flv', 'wmv']

function isVideo(name) {
  const ext = name.split('.').pop()?.toLowerCase()
  return VIDEO_EXTS.includes(ext)
}

// --- Pick folder (click drop zone) ---
async function pickFolder() {
  if (window.showDirectoryPicker) {
    try {
      const dirHandle = await window.showDirectoryPicker()
      // Collect videos grouped by subfolder
      const groups = {} // { categoryName: [File, ...] }
      const rootFiles = []
      emit('folderName', dirHandle.name)
      for await (const entry of dirHandle.values()) {
        if (entry.kind === 'file') {
          const file = await entry.getFile()
          if (isVideo(file.name)) rootFiles.push(file)
        } else if (entry.kind === 'directory') {
          const subFiles = []
          for await (const sub of entry.values()) {
            if (sub.kind === 'file') {
              const file = await sub.getFile()
              if (isVideo(file.name)) subFiles.push(file)
            }
          }
          if (subFiles.length > 0) groups[entry.name] = subFiles
        }
      }
      if (rootFiles.length > 0) groups[dirHandle.name] = rootFiles
      for (const [cat, files] of Object.entries(groups)) {
        await doUpload(files, cat)
      }
      return
    } catch (e) {
      // User cancelled
      return
    }
  }
  // Fallback: traditional <input webkitdirectory>
  folderInput.value?.click()
}

// --- Pick files (click link) ---
async function pickFiles() {
  if (window.showOpenFilePicker) {
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
      return
    } catch (e) {
      // User cancelled
      return
    }
  }
  // Fallback: traditional <input type="file" multiple>
  fileInput.value?.click()
}

// --- Fallback input handlers ---
async function onFolderInputChange(event) {
  const allFiles = Array.from(event.target.files || [])
  const videos = allFiles.filter(f => isVideo(f.name))
  if (videos.length > 0) {
    // Group by parent subfolder via webkitRelativePath
    // e.g. "视频0213/手写/手写1.mp4" → category "手写", parent "视频0213"
    // e.g. "视频0213/file.mp4" → category "视频0213"
    const groups = {}
    const firstPath = (videos[0].webkitRelativePath || '').split('/')
    if (firstPath.length >= 2) emit('folderName', firstPath[0])
    for (const file of videos) {
      const parts = (file.webkitRelativePath || file.name).split('/')
      const cat = parts.length >= 3 ? parts[parts.length - 2] : (parts[0] || defaultCategory)
      if (!groups[cat]) groups[cat] = []
      groups[cat].push(file)
    }
    for (const [cat, files] of Object.entries(groups)) {
      await doUpload(files, cat)
    }
  }
  event.target.value = ''
}

async function onFileInputChange(event) {
  const files = Array.from(event.target.files || []).filter(f => isVideo(f.name))
  if (files.length > 0) {
    await doUpload(files, defaultCategory)
  }
  event.target.value = ''
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
        emit('folderName', entry.name)
        // Check for subdirectories first
        const subGroups = await readDirectoryGrouped(entry)
        for (const [cat, files] of Object.entries(subGroups)) {
          if (files.length > 0) await doUpload(files, cat)
        }
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
async function readDirectoryGrouped(dirEntry) {
  // Returns { categoryName: [File, ...] }
  // If dir has subdirectories with videos, each subdir is a category
  // If dir has direct video files, they go under the dir's own name
  const groups = {}
  const rootFiles = []
  const entries = await readAllEntries(dirEntry)
  for (const entry of entries) {
    if (entry.isFile) {
      const file = await getFileFromEntry(entry)
      if (file && isVideo(file.name)) rootFiles.push(file)
    } else if (entry.isDirectory) {
      const subEntries = await readAllEntries(entry)
      const subFiles = []
      for (const sub of subEntries) {
        if (sub.isFile) {
          const file = await getFileFromEntry(sub)
          if (file && isVideo(file.name)) subFiles.push(file)
        }
      }
      if (subFiles.length > 0) groups[entry.name] = subFiles
    }
  }
  if (rootFiles.length > 0) groups[dirEntry.name] = rootFiles
  return groups
}

function readAllEntries(dirEntry) {
  return new Promise((resolve) => {
    const reader = dirEntry.createReader()
    const result = []
    function readBatch() {
      reader.readEntries((entries) => {
        if (entries.length === 0) { resolve(result); return }
        result.push(...entries)
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
