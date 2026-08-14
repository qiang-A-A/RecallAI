<script setup lang="ts">
/** AI 答疑页:历史对话 + 聊天窗口。 */
import { onMounted, ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { storeToRefs } from 'pinia'
import { useChatStore } from '@/stores'
import type { ChatMessage } from '@/types'
import { renderAiReply } from '@/utils/render-md'

const chat = useChatStore()
const route = useRoute()
const { messages, typing } = storeToRefs(chat)

/** 把 AI 消息渲染成 HTML(Markdown + KaTeX) */
const renderedMessages = computed(() =>
  messages.value.map((m) => ({
    ...m,
    html: m.role === 'ai' ? renderAiReply(m.text) : '',
  })),
)

const input = ref('')
const logRef = ref<HTMLElement>()

const chips = ['帮我讲讲这道题', '圆锥曲线总丢分', '生成变式题']

/** 历史会话分组(按日期:今天 / 昨天 / 更早) */
const groupedChats = computed(() => {
  const groups: { group: string; items: { id: string; title: string; time: string }[] }[] = []
  const today = new Date()
  const dayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate())
  const yesterdayStart = new Date(dayStart.getTime() - 86400_000)
  const push = (group: string, id: string, title: string, time: string) => {
    let g = groups.find((x) => x.group === group)
    if (!g) { g = { group, items: [] }; groups.push(g) }
    g.items.push({ id, title, time })
  }
  for (const c of chat.conversations) {
    const d = new Date(c.created_at)
    const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
    if (d >= dayStart) push('今天', c.id, c.title, hm)
    else if (d >= yesterdayStart) push('昨天', c.id, c.title, hm)
    else push('更早', c.id, c.title, `${d.getMonth() + 1}/${d.getDate()}`)
  }
  return groups
})

onMounted(() => {
  // 恢复本地历史会话(若存在)
  chat.loadConversations()
  if (!messages.value.length && !chat.activeConvId) {
    chat.messages.push({ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' })
  }
  // 支持从其他页面(如数据看板)携带 ?q= 提问过来
  const q = route.query.q
  if (typeof q === 'string' && q.trim()) {
    void chat.send(q)
  }
})

function send() {
  const v = input.value.trim()
  if (!v || typing.value) return
  input.value = ''
  void chat.send(v)
}

function sendChip(c: string) {
  void chat.send(c)
}

/** 新建对话 */
function newChat() {
  chat.newChat()
}

/** 历史对话点击:加载对应会话 */
function openChat(c: { id: string }) {
  chat.openConversation(c.id)
}

/** 删除历史对话 */
function deleteChat(c: { id: string; title: string }, e: Event) {
  e.stopPropagation()
  if (!confirm(`确定删除对话「${c.title}」吗?`)) return
  chat.deleteConversation(c.id)
}

function msgKey(m: ChatMessage, i: number): string {
  return `${m.role}-${i}`
}
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-[216px_1fr] bg-white border border-[#e5e3df]
              rounded-[16px] shadow-xs overflow-hidden min-h-[560px]">
    <!-- 历史对话列表 -->
    <aside class="border-b lg:border-b-0 lg:border-r border-[#e5e3df] bg-[#fafaf9] p-4">
      <button @click="newChat" class="w-full flex items-center justify-center gap-1.5 border-2 border-dashed
                     border-[#c8c4be] rounded-lg py-2 mb-3 text-xs text-steel transition-all
                     hover:border-primary hover:text-primary">
        <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
        新建对话
      </button>
      <template v-if="groupedChats.length" v-for="g in groupedChats" :key="g.group">
        <div class="text-[10.5px] font-semibold text-stone tracking-wider uppercase px-2 pt-3 pb-1">
          {{ g.group }}
        </div>
        <button
          v-for="c in g.items"
          :key="c.id"
          class="group flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-[13px]
                 transition-all text-left text-slate hover:bg-white hover:text-charcoal"
          :class="chat.activeConvId === c.id ? 'bg-tint-lavender text-primary-deep font-semibold' : ''"
          @click="openChat(c)"
        >
          <span class="truncate">{{ c.title }}</span>
          <span class="ml-auto text-[10.5px] text-stone flex-none">{{ c.time }}</span>
          <!-- 删除对话 -->
          <button class="flex-none w-5 h-5 rounded-md flex items-center justify-center
                         text-stone opacity-0 group-hover:opacity-100 hover:bg-error hover:text-white transition-opacity"
                  title="删除对话"
                  @click.stop="deleteChat(c, $event)">
            <svg viewBox="0 0 24 24" class="w-3 h-3" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6" /></svg>
          </button>
        </button>
      </template>
      <!-- 空历史 -->
      <div v-else class="text-center py-6 text-[11.5px] text-stone leading-relaxed">
        <p>暂无历史对话</p>
        <p class="text-[10.5px] mt-0.5">提问后将自动保存到此处</p>
      </div>
    </aside>

    <!-- 聊天窗口 -->
    <div class="p-5 min-w-0 flex flex-col">
      <div class="flex items-center gap-3 pb-3 border-b border-[#e5e3df] mb-3.5">
        <div class="w-10 h-10 rounded-[12px] flex-none flex items-center justify-center
                    bg-gradient-to-br from-ai-start to-ai-end text-white shadow-sm">
          <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor"
               stroke-width="1.8" stroke-linecap="round">
            <path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" />
          </svg>
        </div>
        <div>
          <h3 class="m-0 text-[15.5px] font-semibold text-charcoal">{{ chat.activeTitle }}</h3>
          <p class="m-0 text-[11.5px] text-steel">基于你的错题画像 · 可溯源 · 3 级提示讲解</p>
        </div>
        <span class="ml-auto text-[11px] font-semibold text-white bg-gradient-to-r
                     from-ai-start to-ai-end rounded-full px-2.5 py-0.5">在线</span>
      </div>

      <!-- 欢迎语 -->
      <div class="bg-[rgba(99,102,241,.08)] border border-tint-lavender rounded-[12px]
                  px-4 py-3.5 mb-3.5 text-[13px] text-slate">
        <b class="text-primary-deep">欢迎语:</b><span class="ai-render" v-html="renderAiReply(chat.messages.find(m=>m.role==='ai')?.text || '')" />
      </div>

      <!-- 消息流 -->
      <div ref="logRef" class="flex flex-col gap-3 min-h-[280px] max-h-[430px] overflow-y-auto p-1 mb-3">
        <div
          v-for="(m, i) in renderedMessages"
          :key="msgKey(m, i)"
          class="flex gap-2.5 max-w-[85%] animate-[slideUp_.25s_ease]"
          :class="m.role === 'user' ? 'self-end flex-row-reverse' : ''"
        >
          <div v-if="m.role === 'ai'" class="w-8 h-8 rounded-[10px] flex-none flex items-center justify-center
                       bg-gradient-to-br from-ai-start to-ai-end text-white">
            <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3" /></svg>
          </div>
          <div v-else class="w-8 h-8 rounded-[10px] flex-none flex items-center justify-center
                       bg-tint-sky text-[#005bab] text-[12px] font-semibold">我</div>
          <div
            class="px-4 py-3 rounded-[14px] text-[13.5px] leading-relaxed"
            :class="m.role === 'user'
              ? 'bg-gradient-to-br from-primary to-primary-deep text-white rounded-tr-[4px]'
              : 'bg-white border border-[#e5e3df] shadow-xs rounded-tl-[4px]'"
          >
            <!-- 用户消息:白底反色,等换行原文;AI 消息:Markdown + KaTeX 渲染 -->
            <div v-if="m.role === 'ai'" class="ai-render whitespace-normal" v-html="m.html" />
            <div v-else class="whitespace-pre-wrap">{{ m.text }}</div>
          </div>
        </div>
        <!-- 打字动画 -->
        <div v-if="typing" class="flex gap-2.5">
          <div class="w-8 h-8 rounded-[10px] flex items-center justify-center
                      bg-gradient-to-br from-ai-start to-ai-end text-white">
            <svg viewBox="0 0 24 24" class="w-4 h-4" fill="none" stroke="currentColor"
                 stroke-width="1.8" stroke-linecap="round"><path d="M12 3v3M12 18v3" /></svg>
          </div>
          <div class="bg-white border border-[#e5e3df] rounded-[14px] rounded-tl-[4px] shadow-xs px-4 py-3.5 flex gap-1">
            <i class="w-1.5 h-1.5 rounded-full bg-stone animate-bounce" />
            <i class="w-1.5 h-1.5 rounded-full bg-stone animate-bounce [animation-delay:.2s]" />
            <i class="w-1.5 h-1.5 rounded-full bg-stone animate-bounce [animation-delay:.4s]" />
          </div>
        </div>
      </div>

      <!-- 快捷提问 -->
      <div class="flex gap-2 flex-wrap mb-2">
        <button
          v-for="c in chips"
          :key="c"
          class="text-xs font-medium text-primary-deep bg-tint-lavender rounded-full px-3.5 py-1.5
                 transition-colors hover:bg-[#d6b6f6]"
          @click="sendChip(c)"
        >{{ c }}</button>
      </div>

      <!-- 输入区 -->
      <form class="flex items-center gap-2.5 bg-white border border-[#c8c4be] rounded-[14px]
                   px-4 py-2 shadow-sm" @submit.prevent="send">
        <input
          v-model="input"
          class="flex-1 border-none outline-none text-[13.5px] text-charcoal"
          placeholder="输入你的问题…(支持公式 / 题目粘贴)"
          aria-label="AI 对话输入"
        />
        <button type="submit" aria-label="发送"
                class="w-[38px] h-[38px] rounded-[11px] bg-gradient-to-br from-ai-start to-ai-end
                       text-white flex items-center justify-center transition-transform
                       hover:brightness-105 active:scale-[0.94]">
          <svg viewBox="0 0 24 24" class="w-[17px] h-[17px]" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 2L11 13M22 2l-7 20-4-9-9-4z" />
          </svg>
        </button>
      </form>
    </div>
  </div>
</template>
