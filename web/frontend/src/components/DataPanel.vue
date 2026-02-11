<template>
  <div class="data-page">
    <div class="data-page-header">
      <div>
        <div class="data-page-title">数据追踪</div>
        <div class="data-page-desc">记录每个视频的播放和互动数据</div>
      </div>
    </div>

    <div v-if="loading" class="data-loading">加载中...</div>

    <div v-else-if="filteredVideos.length === 0" class="data-empty">
      暂无数据，处理视频后自动生成
    </div>

    <div v-else class="data-table-wrap">
      <table class="data-table">
        <thead>
          <tr>
            <th class="col-name">视频文件</th>
            <th class="col-date">日期</th>
            <th v-for="col in columns" :key="col.key" class="col-stat">
              <span class="col-icon" v-html="col.svg"></span>
              {{ col.label }}
            </th>
            <th class="col-action"></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="v in filteredVideos" :key="v.id" class="data-row">
            <td class="col-name">
              <span class="data-filename">{{ v.filename }}</span>
            </td>
            <td class="col-date">{{ formatDate(v.created_at) }}</td>
            <td v-for="col in columns" :key="col.key" class="col-stat">
              <input
                class="stat-input"
                type="number"
                :placeholder="'-'"
                :value="v.stats[col.key] ?? ''"
                @change="onStatChange(v, col.key, $event.target.value)"
              />
            </td>
            <td class="col-action">
              <button
                v-if="dirty[v.id]"
                class="btn-save-row"
                @click="saveRow(v)"
              >保存</button>
              <span v-else class="save-ok">&#10003;</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'

const props = defineProps({
  platform: { type: String, default: 'weixin' },
})

const loading = ref(true)
const videos = ref([])
const dirty = reactive({})

// --- SVG Icons (14px, single-color, stroke-based) ---
const I = {
  // ▶ 播放
  play: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="4,2 12,7 4,12" fill="currentColor" stroke="none"/></svg>',
  // 👍 大拇指
  thumb: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 6.5V12H2.5a1 1 0 01-1-1V7.5a1 1 0 011-1H4zm0 0l2-5a1.5 1.5 0 011.5-1h.3a1 1 0 011 1V5h2.7a1 1 0 011 1.1l-.8 5a1 1 0 01-1 .9H4"/></svg>',
  // ❤ 爱心
  heart: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M7 12S1.5 8.5 1.5 5a2.5 2.5 0 015.5.5A2.5 2.5 0 0112.5 5C12.5 8.5 7 12 7 12z"/></svg>',
  // 💬 评论
  comment: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M1.5 2.5a1 1 0 011-1h9a1 1 0 011 1v6a1 1 0 01-1 1H5l-2.5 2.5V9.5h-1a1 1 0 01-1-1z"/></svg>',
  // ↗ 转发/分享
  share: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M8 1.5l4 4-4 4"/><path d="M12 5.5H5.5a4 4 0 00-4 4v1"/></svg>',
  // ⭐ 收藏
  star: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M7 1l1.8 3.6L13 5.2l-3 2.9.7 4.1L7 10.3 3.3 12.2l.7-4.1-3-2.9 4.2-.6z"/></svg>',
  // 👥 涨粉
  users: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="5" cy="4" r="2"/><path d="M1 12a4 4 0 018 0"/><circle cx="10" cy="4.5" r="1.5"/><path d="M13 12a3 3 0 00-4.5-2.6"/></svg>',
  // 🪙 投币 (B站)
  coin: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="7" cy="7" r="5.5"/><path d="M5.5 5.5h3M7 5.5v4"/></svg>',
  // 📝 弹幕 (B站)
  danmaku: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="2.5" width="12" height="9" rx="1"/><path d="M3.5 5.5h4M3.5 7.5h7M3.5 9.5h5"/></svg>',
  // 🔁 转发链 (微博)
  repost: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2l2 2-2 2"/><path d="M2 7V6a2 2 0 012-2h8"/><path d="M4 12l-2-2 2-2"/><path d="M12 7v1a2 2 0 01-2 2H2"/></svg>',
  // 👁 曝光 (小红书)
  eye: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M1 7s2.5-4 6-4 6 4 6 4-2.5 4-6 4-6-4-6-4z"/><circle cx="7" cy="7" r="1.5"/></svg>',
  // 📌 收藏 (小红书 pin style)
  pin: '<svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round"><path d="M4 2h6l1 5H3l1-5z"/><path d="M3 7h8"/><path d="M7 7v5"/></svg>',
}

const PLATFORM_COLUMNS = {
  weixin: [
    { key: 'play_count', svg: I.play, label: '播放量' },
    { key: 'thumb_count', svg: I.thumb, label: '私赞' },
    { key: 'heart_count', svg: I.heart, label: '公赞' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
    { key: 'share_count', svg: I.share, label: '转发' },
    { key: 'follower_gain', svg: I.users, label: '涨粉' },
  ],
  douyin: [
    { key: 'play_count', svg: I.play, label: '播放量' },
    { key: 'like_count', svg: I.heart, label: '点赞' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
    { key: 'share_count', svg: I.share, label: '分享' },
    { key: 'favorite_count', svg: I.star, label: '收藏' },
    { key: 'follower_gain', svg: I.users, label: '涨粉' },
  ],
  kuaishou: [
    { key: 'play_count', svg: I.play, label: '播放量' },
    { key: 'like_count', svg: I.heart, label: '双击' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
    { key: 'share_count', svg: I.share, label: '分享' },
    { key: 'favorite_count', svg: I.star, label: '收藏' },
    { key: 'follower_gain', svg: I.users, label: '涨粉' },
  ],
  xiaohongshu: [
    { key: 'impression_count', svg: I.eye, label: '曝光量' },
    { key: 'play_count', svg: I.play, label: '观看量' },
    { key: 'like_count', svg: I.heart, label: '点赞' },
    { key: 'favorite_count', svg: I.pin, label: '收藏' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
    { key: 'share_count', svg: I.share, label: '分享' },
    { key: 'follower_gain', svg: I.users, label: '涨粉' },
  ],
  bilibili: [
    { key: 'play_count', svg: I.play, label: '播放量' },
    { key: 'like_count', svg: I.thumb, label: '点赞' },
    { key: 'coin_count', svg: I.coin, label: '投币' },
    { key: 'favorite_count', svg: I.star, label: '收藏' },
    { key: 'share_count', svg: I.share, label: '分享' },
    { key: 'danmaku_count', svg: I.danmaku, label: '弹幕' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
  ],
  weibo: [
    { key: 'play_count', svg: I.play, label: '播放量' },
    { key: 'like_count', svg: I.heart, label: '点赞' },
    { key: 'repost_count', svg: I.repost, label: '转发' },
    { key: 'comment_count', svg: I.comment, label: '评论' },
    { key: 'favorite_count', svg: I.star, label: '收藏' },
    { key: 'follower_gain', svg: I.users, label: '涨粉' },
  ],
  youtube: [
    { key: 'play_count', svg: I.play, label: 'Views' },
    { key: 'like_count', svg: I.thumb, label: 'Likes' },
    { key: 'comment_count', svg: I.comment, label: 'Comments' },
    { key: 'share_count', svg: I.share, label: 'Shares' },
    { key: 'subscriber_gain', svg: I.users, label: 'Subscribers' },
  ],
  tiktok: [
    { key: 'play_count', svg: I.play, label: 'Views' },
    { key: 'like_count', svg: I.heart, label: 'Likes' },
    { key: 'comment_count', svg: I.comment, label: 'Comments' },
    { key: 'share_count', svg: I.share, label: 'Shares' },
    { key: 'favorite_count', svg: I.star, label: 'Saves' },
    { key: 'follower_gain', svg: I.users, label: 'Followers' },
  ],
  instagram: [
    { key: 'play_count', svg: I.play, label: 'Views' },
    { key: 'like_count', svg: I.heart, label: 'Likes' },
    { key: 'comment_count', svg: I.comment, label: 'Comments' },
    { key: 'share_count', svg: I.share, label: 'Shares' },
    { key: 'save_count', svg: I.star, label: 'Saves' },
    { key: 'follower_gain', svg: I.users, label: 'Followers' },
  ],
  facebook: [
    { key: 'play_count', svg: I.play, label: 'Views' },
    { key: 'like_count', svg: I.thumb, label: 'Likes' },
    { key: 'comment_count', svg: I.comment, label: 'Comments' },
    { key: 'share_count', svg: I.share, label: 'Shares' },
    { key: 'follower_gain', svg: I.users, label: 'Followers' },
  ],
  twitter: [
    { key: 'impression_count', svg: I.eye, label: 'Impressions' },
    { key: 'like_count', svg: I.heart, label: 'Likes' },
    { key: 'repost_count', svg: I.repost, label: 'Reposts' },
    { key: 'comment_count', svg: I.comment, label: 'Replies' },
    { key: 'follower_gain', svg: I.users, label: 'Followers' },
  ],
}

const columns = computed(() => PLATFORM_COLUMNS[props.platform] || PLATFORM_COLUMNS.weixin)

const filteredVideos = computed(() =>
  videos.value.filter(v => v.platform === props.platform)
)

function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  const hh = String(d.getHours()).padStart(2, '0')
  const mi = String(d.getMinutes()).padStart(2, '0')
  return `${mm}-${dd} ${hh}:${mi}`
}

function onStatChange(video, key, value) {
  const num = value === '' ? null : Number(value)
  if (!video.stats) video.stats = {}
  video.stats[key] = num
  dirty[video.id] = true
}

async function saveRow(video) {
  await fetch('/api/video-stats', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ id: video.id, stats: video.stats }),
  })
  delete dirty[video.id]
}

onMounted(async () => {
  try {
    const res = await fetch('/api/video-stats')
    const data = await res.json()
    videos.value = data.videos || []
  } catch (e) {}
  loading.value = false
})
</script>
