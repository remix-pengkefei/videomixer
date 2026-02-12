<template>
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="sidebar-logo">VM</span>
      <span class="sidebar-title">VideoMixer</span>
    </div>

    <div class="sidebar-section-label">国内平台</div>

    <nav class="sidebar-nav">
      <button
        v-for="p in domesticPlatforms"
        :key="p.id"
        :class="['sidebar-item', { active: p.id === activePlatform, disabled: !p.enabled }]"
        :disabled="!p.enabled"
        @click="p.enabled && $emit('selectPlatform', p.id)"
      >
        <span class="sidebar-item-icon" v-html="p.svg"></span>
        <span class="sidebar-item-name">{{ p.name }}</span>
        <span v-if="!p.enabled" class="sidebar-item-badge">即将上线</span>
      </button>
    </nav>

    <div class="sidebar-section-label">海外平台</div>

    <nav class="sidebar-nav">
      <button
        v-for="p in overseaPlatforms"
        :key="p.id"
        :class="['sidebar-item', { active: p.id === activePlatform, disabled: !p.enabled }]"
        :disabled="!p.enabled"
        @click="p.enabled && $emit('selectPlatform', p.id)"
      >
        <span class="sidebar-item-icon" v-html="p.svg"></span>
        <span class="sidebar-item-name">{{ p.name }}</span>
        <span v-if="!p.enabled" class="sidebar-item-badge">即将上线</span>
      </button>
    </nav>

    <div class="sidebar-footer">
      <div class="sidebar-version">v1.0</div>
    </div>
  </aside>
</template>

<script setup>
defineProps({
  activePlatform: { type: String, default: 'weixin' },
})

defineEmits(['selectPlatform'])

// 16x16 SVG icons, single-color stroke style
const S = {
  // 视频号 — TV/monitor with play button
  weixin: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="2" width="13" height="9" rx="1.5"/><path d="M6.5 5v4l3.5-2-3.5-2z"/><path d="M5.5 13h5"/></svg>',
  // 抖音 — music note
  douyin: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v8.5a2.5 2.5 0 11-2-2.45V2h2z"/><path d="M10 4.5c1.5.5 3 .5 4 0"/></svg>',
  // 快手 — lightning bolt
  kuaishou: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 1.5L4 9h4l-1 5.5L12 7H8l1-5.5z"/></svg>',
  // 小红书 — book/note with heart
  xiaohongshu: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="1.5" width="10" height="13" rx="1.5"/><path d="M8 6.5S6.5 5 5.5 6s1 2.5 2.5 4c1.5-1.5 3-3 2.5-4s-2.5.5-2.5.5z"/></svg>',
  // B站 — TV with antenna
  bilibili: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M4.5 4L6 2M11.5 4L10 2"/><rect x="1.5" y="4" width="13" height="9" rx="2"/><circle cx="5.5" cy="8.5" r="1"/><circle cx="10.5" cy="8.5" r="1"/></svg>',
  // 微博 — speech bubble with wave
  weibo: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M2 10c0 2.5 3 4 6 4s6-1.5 6-4-3-4-6-4-6 1.5-6 4z"/><path d="M11 3.5c1 0 2 .5 2.5 1.5"/><path d="M11.5 1c1.5 0 3 1 3.5 2.5"/></svg>',
  // YouTube — play button in rounded rect
  youtube: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="3" width="13" height="10" rx="3"/><path d="M6.5 6v4l4-2-4-2z"/></svg>',
  // TikTok — music note variant
  tiktok: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M9 1.5v9a2.5 2.5 0 11-2-2.45V1.5h2z"/><path d="M9 3.5a4 4 0 004 0v2a6 6 0 01-4 0"/></svg>',
  // Instagram — camera with lens
  instagram: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="1.5" width="13" height="13" rx="3.5"/><circle cx="8" cy="8" r="3"/><circle cx="12" cy="4" r="0.8" fill="currentColor" stroke="none"/></svg>',
  // Facebook — f letter style
  facebook: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="1.5" y="1.5" width="13" height="13" rx="3.5"/><path d="M10.5 1.5V5H12M6.5 14.5V9h5M6.5 9V6.5a2 2 0 012-2h2"/></svg>',
  // X/Twitter — stylized X
  twitter: '<svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M3 3l10 10M13 3L3 13"/></svg>',
}

const domesticPlatforms = [
  { id: 'weixin', name: '视频号', svg: S.weixin, enabled: true },
  { id: 'douyin', name: '抖音', svg: S.douyin, enabled: false },
  { id: 'kuaishou', name: '快手', svg: S.kuaishou, enabled: false },
  { id: 'xiaohongshu', name: '小红书', svg: S.xiaohongshu, enabled: false },
  { id: 'bilibili', name: 'B站', svg: S.bilibili, enabled: false },
  { id: 'weibo', name: '微博', svg: S.weibo, enabled: false },
]

const overseaPlatforms = [
  { id: 'youtube', name: 'YouTube', svg: S.youtube, enabled: false },
  { id: 'tiktok', name: 'TikTok', svg: S.tiktok, enabled: false },
  { id: 'instagram', name: 'Instagram', svg: S.instagram, enabled: false },
  { id: 'facebook', name: 'Facebook', svg: S.facebook, enabled: false },
  { id: 'twitter', name: 'X (Twitter)', svg: S.twitter, enabled: false },
]
</script>
