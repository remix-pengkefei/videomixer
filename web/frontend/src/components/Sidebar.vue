<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="sidebar-logo">VM</span>
      <span class="sidebar-title">VideoMixer</span>
    </div>

    <div class="sidebar-section-label">平台</div>

    <nav class="sidebar-nav">
      <button
        v-for="p in platforms"
        :key="p.id"
        :class="['sidebar-item', { active: p.id === activePlatform, disabled: !p.enabled }]"
        :disabled="!p.enabled"
        @click="p.enabled && $emit('selectPlatform', p.id)"
      >
        <span class="sidebar-item-icon">{{ p.icon }}</span>
        <span class="sidebar-item-name">{{ p.name }}</span>
        <span v-if="!p.enabled" class="sidebar-item-badge">即将上线</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <div v-if="updateInfo" class="sidebar-update" @click="$emit('showUpdate')">
        <span class="sidebar-update-dot"></span>
        有新版本可用
      </div>
      <div class="sidebar-version">v1.0.0</div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  activePlatform: { type: String, default: 'weixin' },
  updateInfo: { type: Object, default: null },
})

defineEmits(['selectPlatform', 'showUpdate'])

const platforms = [
  { id: 'weixin', name: '视频号', icon: '📺', enabled: true },
  { id: 'douyin', name: '抖音', icon: '🎵', enabled: false },
  { id: 'kuaishou', name: '快手', icon: '⚡', enabled: false },
  { id: 'xiaohongshu', name: '小红书', icon: '📕', enabled: false },
  { id: 'bilibili', name: 'B站', icon: '📹', enabled: false },
  { id: 'weibo', name: '微博', icon: '💬', enabled: false },
]
</script>
