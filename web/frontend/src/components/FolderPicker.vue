<template>
  <div :class="compact ? '' : 'card'">
    <div v-if="label && !compact" class="card-title">{{ label }}</div>
    <div class="folder-row">
      <div class="folder-path" :class="{ placeholder: !path }">
        {{ path || placeholder }}
      </div>
      <button class="btn btn-secondary btn-sm" @click="showModal = true">选择</button>
    </div>
  </div>

  <!-- Folder browser modal -->
  <teleport to="body">
    <div v-if="showModal" class="modal-overlay" @click.self="showModal = false">
      <div class="modal">
        <div class="modal-header">
          <span class="modal-title">选择文件夹</span>
          <button class="modal-close" @click="showModal = false">&times;</button>
        </div>

        <!-- Breadcrumb -->
        <div class="breadcrumb">
          <button
            v-for="(seg, i) in breadcrumbs"
            :key="i"
            class="breadcrumb-item"
            :class="{ 'breadcrumb-current': i === breadcrumbs.length - 1 }"
            @click="navigateTo(seg.path)"
          >
            {{ seg.name }}
          </button>
        </div>

        <div class="modal-body">
          <!-- Parent directory -->
          <div
            v-if="parentPath"
            class="folder-list-item"
            @click="navigateTo(parentPath)"
          >
            <span class="folder-list-icon">&larrhk;</span>
            <span class="folder-list-name">..</span>
          </div>

          <!-- Subdirectories -->
          <div
            v-for="dir in dirs"
            :key="dir.path"
            class="folder-list-item"
            @click="navigateTo(dir.path)"
          >
            <span class="folder-list-icon folder-list-icon-dir"></span>
            <span class="folder-list-name">{{ dir.name }}</span>
          </div>

          <!-- Video files (info only) -->
          <div
            v-for="file in files"
            :key="file.path"
            class="folder-list-item"
            style="opacity: 0.5; cursor: default;"
          >
            <span class="folder-list-icon folder-list-icon-file"></span>
            <span class="folder-list-name">{{ file.name }}</span>
          </div>

          <div v-if="dirs.length === 0 && files.length === 0" class="empty-state">
            此目录为空
          </div>
        </div>

        <div class="modal-footer">
          <div class="modal-footer-path">{{ currentPath }}</div>
          <button class="btn btn-primary" @click="confirmSelection">选择此文件夹</button>
        </div>
      </div>
    </div>
  </teleport>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

const props = defineProps({
  label: String,
  path: String,
  placeholder: String,
  compact: { type: Boolean, default: false },
})

const emit = defineEmits(['select'])

const showModal = ref(false)
const currentPath = ref('')
const parentPath = ref(null)
const dirs = ref([])
const files = ref([])
const loading = ref(false)

const breadcrumbs = computed(() => {
  if (!currentPath.value) return []
  const parts = currentPath.value.split('/').filter(Boolean)
  const crumbs = [{ name: '/', path: '/' }]
  let accumulated = ''
  for (const part of parts) {
    accumulated += '/' + part
    crumbs.push({ name: part, path: accumulated })
  }
  return crumbs
})

watch(showModal, (val) => {
  if (val) {
    const startPath = props.path || '/Users'
    navigateTo(startPath)
  }
})

async function navigateTo(path) {
  loading.value = true
  try {
    const res = await fetch(`/api/folders?path=${encodeURIComponent(path)}`)
    const data = await res.json()
    currentPath.value = data.path
    parentPath.value = data.parent
    dirs.value = data.dirs
    files.value = data.files
  } catch (e) {
    console.error('Failed to browse folder:', e)
  }
  loading.value = false
}

function confirmSelection() {
  emit('select', currentPath.value)
  showModal.value = false
}
</script>
