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

const chats = [
  { group: '今天', items: [{ t: '导数单调区间讲解', time: '10:20' }, { t: '圆锥曲线总丢分怎么办', time: '09:41' }] },
  { group: '昨天', items: [{ t: '受力分析错因诊断', time: '21:05' }, { t: '生成 3 道变式题', time: '19:32' }] },
  { group: '更早', items: [{ t: '英语时态答疑', time: '8/9' }, { t: '复习计划咨询', time: '8/7' }] },
]

const chips = ['帮我讲讲这道题', '圆锥曲线总丢分', '生成变式题']

onMounted(() => {
  if (!messages.value.length) {
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

/** 新建对话:清空消息并恢复欢迎语 */
function newChat() {
  chat.newChat()
}

/** 历史对话点击:加载对应的预设会话记录 */
function openChat(c: { t: string }) {
  chat.activeTitle = c.t
  const presets: Record<string, ChatMessage[]> = {
    '导数单调区间讲解': [
      { role: 'user', text: '帮我讲讲导数求单调区间的方法' },
      { role: 'ai', text: '求单调区间三步:① 求导 f\'(x);② 令 f\'(x)=0 找驻点;③ 列表判定符号。以 f(x)=x³−3x²+1 为例,f\'(x)=3x²−6x=3x(x−2),驻点 0 和 2,单调递减区间为 (0,2)。' },
    ],
    '圆锥曲线总丢分怎么办': [
      { role: 'user', text: '圆锥曲线总丢分怎么办?' },
      { role: 'ai', text: '圆锥曲线丢分集中在联立方程与判别式。建议:① 先把「设而不求、韦达定理」套路写熟;② 判别式 Δ 判断交点个数别忘;③ 每道题固定答题框架,减少计算失误。需要我给你出一组专项训练吗?' },
    ],
    '受力分析错因诊断': [
      { role: 'user', text: '帮我诊断受力分析的常见错因' },
      { role: 'ai', text: '受力分析错因 TOP3:① 漏力(摩擦力方向判断错误);② 多力(把合力当分力);③ 正交分解角度代错。建议每次画受力图后按「重力→弹力→摩擦力→其他」顺序核对一遍。' },
    ],
  }
  chat.messages = presets[c.t] ?? [
    { role: 'user', text: c.t },
    { role: 'ai', text: `关于「${c.t}」:这是你之前的提问记录。我可以继续讲解或重新梳理,直接告诉我你想深入的方向。` },
  ]
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
      <template v-for="g in chats" :key="g.group">
        <div class="text-[10.5px] font-semibold text-stone tracking-wider uppercase px-2 pt-3 pb-1">
          {{ g.group }}
        </div>
        <button
          v-for="c in g.items"
          :key="c.t"
          class="flex items-center gap-2 w-full px-2.5 py-2 rounded-lg text-[13px]
                 transition-all text-left text-slate hover:bg-white hover:text-charcoal"
          @click="openChat(c)"
        >
          <span>{{ c.t }}</span><span class="ml-auto text-[10.5px] text-stone">{{ c.time }}</span>
        </button>
      </template>
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
