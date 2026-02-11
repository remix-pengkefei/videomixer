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
          :class="{ active: currentTab === 'history' }"
          @click="$emit('changeTab', 'history')"
        >
          记录
        </button>
      </nav>
    </div>
  </header>
</template>

<script setup>
defineProps({
  currentTab: String,
})

defineEmits(['changeTab'])
</script>
