<script setup lang="ts">
/** 顶部导航组件:品牌 + 4 个 Tab + 搜索 + 头像。 */
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

const navs = [
  { key: 'questions', label: '错题集', icon: 'M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z' },
  { key: 'ai', label: 'AI 答疑', icon: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z' },
  { key: 'analytics', label: '数据看板', icon: 'M3 3v18h18M18 17V9M13 17V5M8 17v-3' },
  { key: 'help', label: '帮助', icon: 'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01' },
  { key: 'settings', label: '设置', icon: 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09a1.65 1.65 0 0 0 1.51-1 1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33h.01a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51h.01a1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82v.01a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z' },
]

function isActive(key: string): boolean {
  return route.name === key
}
</script>

<template>
  <nav class="sticky top-0 z-50 h-[60px] flex items-center gap-0.5 sm:gap-1.5 px-3 sm:px-6
              bg-white/95 backdrop-blur-md border-b border-[#e5e3df] overflow-x-auto">
    <div class="flex items-center gap-1.5 sm:gap-2.5 mr-2 sm:mr-5 flex-none">
      <div class="w-8 h-8 rounded-[9px] bg-gradient-to-br from-primary to-ai-end
                  flex items-center justify-center text-white flex-none">
        <svg viewBox="0 0 24 24" class="w-[17px] h-[17px]" fill="none" stroke="currentColor"
             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
        </svg>
      </div>
      <span class="hidden sm:inline text-[15px] font-bold text-charcoal tracking-tight">Recall</span>
    </div>

    <button
      v-for="n in navs"
      :key="n.key"
      class="flex items-center justify-center gap-1.5 px-2 sm:px-3.5 py-2 rounded-lg text-[13.5px] font-medium transition-all flex-none"
      :class="isActive(n.key) ? 'bg-tint-lavender text-primary-deep font-semibold' : 'text-slate hover:bg-[#f6f5f4] hover:text-charcoal'"
      @click="router.push({ name: n.key })"
    >
      <svg viewBox="0 0 24 24" class="w-[17px] h-[17px]" fill="none" stroke="currentColor"
           stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
        <path :d="n.icon" />
      </svg>
      <span class="hidden sm:inline">{{ n.label }}</span>
    </button>

    <div class="ml-auto flex items-center gap-2.5 flex-none">
      <div class="w-8 h-8 rounded-full bg-tint-sky text-[#005bab] flex items-center justify-center
                  text-[13px] font-semibold" title="考研冲刺中">林</div>
    </div>
  </nav>
</template>
