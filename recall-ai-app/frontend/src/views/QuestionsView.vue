<script setup lang="ts">
/** 错题集主页:分类导航 + 操作栏 + 错题卡片列表。 */
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import AppButton from '@/components/ui/AppButton.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppCard from '@/components/ui/AppCard.vue'
import { useQuestionStore } from '@/stores'
import type { Question } from '@/types'

const store = useQuestionStore()
// 用 ref 镜像 store 状态(避免 Pinia getter 类型推断导致 storeToRefs 返回 Ref<Question[] | undefined>)
// 命名为顶层 ref,模板中会自动解包为数组;computed 内部用 .value
const items = ref<Question[]>([])
const loading = ref(false)
const error = ref('')
watch(() => store.items, (v) => { items.value = Array.isArray(v) ? v : [] }, { immediate: true, deep: true })
watch(() => store.loading, (v) => { loading.value = !!v }, { immediate: true })
watch(() => store.error, (v) => { error.value = v || '' }, { immediate: true })

const activeCat = ref('all')
const keyword = ref('')

// 预置学科分类;数量从 store 数据动态统计
const BASE_CATS = [
  { key: '数学', label: '数学', color: 'bg-tint-lavender text-primary-deep' },
  { key: '物理', label: '物理', color: 'bg-tint-sky text-[#005bab]' },
  { key: '化学', label: '化学', color: 'bg-tint-mint text-[#0a6b1f]' },
  { key: '英语', label: '英语', color: 'bg-tint-mint text-[#0a6b1f]' },
  { key: '生物', label: '生物', color: 'bg-tint-peach text-[#9c3f00]' },
  { key: '语文', label: '语文', color: 'bg-tint-yellow text-[#7a6400]' },
]

// 自定义错题本(新增的)持久化到 localStorage
const customCats = ref<{ key: string; label: string }[]>([])
function loadCustomCats() {
  try {
    const raw = localStorage.getItem('recall_custom_cats')
    if (raw) customCats.value = JSON.parse(raw)
  } catch { /* ignore */ }
}
function saveCustomCats() {
  try { localStorage.setItem('recall_custom_cats', JSON.stringify(customCats.value)) } catch { /* ignore */ }
}
loadCustomCats()

const showNewCat = ref(false)
const newCatName = ref('')
function openNewCat() {
  newCatName.value = ''
  showNewCat.value = true
}
function confirmNewCat() {
  const name = newCatName.value.trim()
  if (!name) return
  if (customCats.value.some((c) => c.label === name)) { alert('该分类已存在'); return }
  customCats.value.push({ key: `cat-${Date.now()}`, label: name })
  saveCustomCats()
  showNewCat.value = false
}

/** 删除自定义错题本(学科内置分类不可删) */
function removeCat(c: { key: string; label: string }) {
  if (!confirm(`确定删除错题本「${c.label}」吗?`)) return
  customCats.value = customCats.value.filter((x) => x.key !== c.key)
  saveCustomCats()
  if (activeCat.value === c.key) activeCat.value = 'all'
}

// 分类列表:全部 + 学科(带动态数量)+ 自定义错题本
const categories = computed(() => {
  const subjectCounts = new Map<string, number>()
  for (const q of items.value) {
    subjectCounts.set(q.subject, (subjectCounts.get(q.subject) ?? 0) + 1)
  }
  const cats: { key: string; label: string; count: number; color: string; custom?: boolean }[] = [
    { key: 'all', label: '全部错题', count: items.value.length, color: 'bg-tint-lavender text-primary-deep' },
    ...BASE_CATS.map((c) => ({ ...c, count: subjectCounts.get(c.key) ?? 0 })),
    ...customCats.value.map((c) => ({ key: c.key, label: c.label, count: 0, color: 'bg-[#f6f5f4] text-stone', custom: true })),
  ]
  return cats
})

const filtered = computed(() =>
  items.value.filter((q: Question) => {
    const cat = categories.value.find((c) => c.key === activeCat.value)
    const catMatch = activeCat.value === 'all' || (cat?.custom ? false : q.subject === activeCat.value)
    return catMatch && (!keyword.value || q.content_json.text.includes(keyword.value))
  }),
)

function masteryColor(m = 0): string {
  // mastery 是 0-1 范围(masteryState.last_status → base 0.3/0.5/0.7 + reps 加成)
  return m >= 0.7 ? 'bg-success' : m >= 0.4 ? 'bg-warning' : 'bg-error'
}

/** 生成 AI 解析摘要:优先后端 ai_summary,否则用识别结果(知识点+错因+答案)动态组合 */
function aiSummary(q: Question): string {
  if (q.ai_summary) return q.ai_summary
  const kp = q.kps?.[0]?.name || ''
  const parts: string[] = []
  if (kp) parts.push(`考点:${kp}`)
  if (q.wrong_reason) parts.push(`错因:${q.wrong_reason}`)
  if (q.answer) parts.push(`答案:${q.answer}`)
  return parts.join(' · ')
}

/** 按 mastery 数值映射掌握状态文本(0-1 → 未掌握/模糊/已掌握) */
function masteryStatus(m = 0): { text: string; variant: 'error' | 'warn' | 'done' } {
  if (m >= 0.7) return { text: '已掌握', variant: 'done' }
  if (m >= 0.4) return { text: '模糊', variant: 'warn' }
  return { text: '未掌握', variant: 'error' }
}

onMounted(() => store.fetchAll())
</script>

<template>
  <div class="grid grid-cols-1 lg:grid-cols-[216px_1fr] bg-white border border-[#e5e3df]
              rounded-[16px] shadow-xs overflow-hidden min-h-[560px]">
    <!-- 左侧分类导航 -->
    <aside class="border-b lg:border-b-0 lg:border-r border-[#e5e3df] bg-[#fafaf9] p-4">
      <div class="flex items-center justify-between px-2 pb-2.5 border-b border-[#e5e3df] mb-2.5">
        <span class="text-xs font-bold text-charcoal">错题分类</span>
        <AppBadge variant="gray">{{ items.length }}</AppBadge>
      </div>
      <div class="flex flex-wrap lg:flex-col gap-0.5">
        <button
          v-for="c in categories"
          :key="c.key"
          class="group flex items-center gap-2 px-2.5 py-2 rounded-lg text-[13px] transition-all text-left"
          :class="activeCat === c.key ? 'bg-tint-lavender text-primary-deep font-semibold' : 'text-slate hover:bg-white hover:text-charcoal'"
          @click="activeCat = c.key"
        >
          <span class="w-[26px] h-[26px] rounded-lg flex items-center justify-center text-[11px] font-bold flex-none"
                :class="c.color">{{ c.label[0] }}</span>
          <span class="truncate">{{ c.label }}</span>
          <span class="ml-auto text-[11px] font-semibold text-stone bg-white border border-[#e5e3df]
                       rounded-full px-1.5 flex-none">{{ c.count }}</span>
          <!-- 自定义错题本:可删除 -->
          <button v-if="c.custom" class="flex-none w-5 h-5 rounded-md flex items-center justify-center
                         text-stone opacity-0 group-hover:opacity-100 hover:bg-error hover:text-white transition-opacity"
                  title="删除错题本"
                  @click.stop="removeCat(c)">
            <svg viewBox="0 0 24 24" class="w-3 h-3" fill="none" stroke="currentColor"
                 stroke-width="2" stroke-linecap="round"><path d="M3 6h18M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6M10 11v6M14 11v6" /></svg>
          </button>
        </button>
      </div>
      <button class="mt-3 w-full flex items-center justify-center gap-1.5 border-2 border-dashed
                     border-[#c8c4be] rounded-lg py-2 text-xs text-steel transition-all
                     hover:border-primary hover:text-primary"
              @click="openNewCat">
        <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
        新增错题本
      </button>
    </aside>

    <!-- 右侧内容区 -->
    <div class="p-5 min-w-0">
      <!-- 操作栏 -->
      <div class="flex flex-wrap items-center gap-2 pb-3.5 border-b border-[#e5e3df] mb-4">
        <AppButton variant="primary" size="sm" @click="$emit('record')">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
          录入错题
        </AppButton>
        <AppButton variant="secondary" size="sm" @click="$emit('review')">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="currentColor"><path d="M5 3l14 9-14 9z" /></svg>
          开始复习
        </AppButton>
        <AppButton variant="secondary" size="sm" @click="$emit('export')">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor"
               stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
          </svg>
          导出
        </AppButton>
        <div class="ml-auto flex items-center gap-2 bg-[#fafaf9] border border-[#e5e3df]
                    rounded-full px-3 py-1.5 min-w-[160px]">
          <svg viewBox="0 0 24 24" class="w-3.5 h-3.5 text-stone" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
            <circle cx="11" cy="11" r="8" /><path d="M21 21l-4.35-4.35" />
          </svg>
          <input v-model="keyword" class="bg-transparent border-none outline-none text-xs w-full"
                 placeholder="搜索题目 / 知识点…" aria-label="搜索错题" />
        </div>
      </div>

      <!-- 加载态 -->
      <div v-if="loading" class="space-y-2.5">
        <div v-for="i in 3" :key="i"
             class="h-24 rounded-xl bg-gradient-to-r from-[#f6f5f4] via-[#ece9e4] to-[#f6f5f4]
                    bg-[length:200%_100%] animate-pulse" />
      </div>

      <!-- 空态 -->
      <div v-else-if="!filtered.length" class="text-center py-14 text-steel">
        <div class="w-14 h-14 rounded-[16px] bg-[#f6f5f4] flex items-center justify-center mx-auto mb-3.5 text-stone">
          <svg viewBox="0 0 24 24" class="w-6 h-6" fill="none" stroke="currentColor"
               stroke-width="1.6" stroke-linecap="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M18.4 5.6l-2.1 2.1M7.7 16.3l-2.1 2.1" /></svg>
        </div>
        <b class="block text-sm text-charcoal mb-1">没有匹配的错题</b>
        <p class="text-xs mb-4">试试调整筛选条件,或录入一道新错题。</p>
        <AppButton variant="primary" size="sm" @click="$emit('record')">录入错题</AppButton>
      </div>

      <!-- 错题卡片列表 -->
      <div v-else class="flex flex-col gap-2.5">
        <div
          v-for="q in filtered"
          :key="q.id"
          class="flex items-start gap-3.5 p-3.5 bg-white border border-[#e5e3df] rounded-[12px]
                 shadow-xs transition-all cursor-pointer hover:shadow-md hover:-translate-y-[1px]
                 hover:border-[#c8c4be]"
          @click="$emit('detail', q)"
        >
          <div class="w-[38px] h-[38px] rounded-[10px] flex items-center justify-center
                      text-[13px] font-bold flex-none"
               :class="{ 'bg-tint-lavender text-primary-deep': q.subject === '数学',
                         'bg-tint-sky text-[#005bab]': q.subject === '物理',
                         'bg-tint-mint text-[#0a6b1f]': q.subject === '英语' }">
            {{ q.subject[0] }}
          </div>
          <div class="flex-1 min-w-0">
            <p class="text-[13.5px] font-medium text-charcoal leading-relaxed mb-1.5
                      line-clamp-2">{{ q.content_json.text }}</p>
            <div class="flex items-center gap-2 flex-wrap mb-1.5">
              <AppBadge variant="ai">{{ q.kps?.[0]?.name || '待确认' }}</AppBadge>
              <span class="flex items-center gap-1 text-[11px] font-semibold tabular-nums">
                <span class="w-2 h-2 rounded-full inline-block" :class="masteryColor(q.mastery)" />
                {{ Math.round((q.mastery ?? 0) * 100) }}%
              </span>
              <span class="text-[11.5px] text-stone">{{ q.created_at.slice(0, 10) }}</span>
            </div>
            <!-- AI 解析行:优先 ai_summary,否则用考点+错因+答案动态组合 -->
            <div v-if="aiSummary(q)"
                 class="border-l-[3px] border-[#6366f1] bg-[#fafaf9] rounded-r-lg px-2.5 py-1.5
                            mt-2 text-xs text-slate flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="w-3 h-3 text-ai-end flex-none" fill="none" stroke="currentColor"
                   stroke-width="1.6" stroke-linecap="round"><path d="M12 3v3M12 18v3M3 12h3M18 12h3" /></svg>
              <span class="line-clamp-2"><b class="text-primary-deep">AI 解析:</b>{{ aiSummary(q) }}</span>
            </div>
            <div v-else
                 class="border border-dashed border-[#c8c4be] rounded-r-lg px-2.5 py-1.5
                            mt-2 text-[11px] text-stone flex items-center gap-1.5">
              <svg viewBox="0 0 24 24" class="w-3 h-3 flex-none" fill="none" stroke="currentColor"
                   stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="12" cy="12" r="9"/><path d="M9 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3M12 17h.01" />
              </svg>
              <span>该题暂无 AI 解析(在 <b class="text-primary">AI 答疑</b> 对话可生成讲解)</span>
            </div>
            <div class="flex items-center gap-2.5 border-t border-dashed border-[#e5e3df] pt-2 mt-2">
              <span class="text-[11.5px] text-stone">复习
                <b class="tabular-nums">{{ q.error_count }}</b> 次</span>
              <div class="ml-auto flex items-center gap-1">
                <!-- 标记掌握度:用户主动决定,实时联动看板 -->
                <div class="flex gap-0.5 mr-1.5 border border-[#e5e3df] rounded-md overflow-hidden">
                  <button class="text-[10.5px] px-1.5 py-0.5 transition"
                          :class="q.mastery >= 0.7 ? 'bg-success text-white font-semibold' : 'text-stone hover:bg-success/10'"
                          title="标记已掌握"
                          @click.stop="store.setMastery(q.id, 'mastered')">已掌握</button>
                  <button class="text-[10.5px] px-1.5 py-0.5 border-l border-r border-[#e5e3df] transition"
                          :class="q.mastery >= 0.4 && q.mastery < 0.7 ? 'bg-warning text-white font-semibold' : 'text-stone hover:bg-warning/10'"
                          title="标记模糊"
                          @click.stop="store.setMastery(q.id, 'fuzzy')">模糊</button>
                  <button class="text-[10.5px] px-1.5 py-0.5 transition"
                          :class="q.mastery < 0.4 ? 'bg-error text-white font-semibold' : 'text-stone hover:bg-error/10'"
                          title="标记未掌握"
                          @click.stop="store.setMastery(q.id, 'failed')">未掌握</button>
                </div>
                <button class="text-xs text-slate hover:text-charcoal px-2 py-0.5 rounded-md
                               hover:bg-[#f6f5f4]"
                        @click.stop="$emit('edit', q)">编辑</button>
                <button class="text-xs text-error px-2 py-0.5 rounded-md hover:bg-[#fde0ec]"
                        @click.stop="$emit('remove', q)">删除</button>
              </div>
            </div>
          </div>
          <div class="flex-none">
            <AppBadge :variant="masteryStatus(q.mastery).variant">
              {{ masteryStatus(q.mastery).text }}
            </AppBadge>
          </div>
        </div>
      </div>

      <!-- 错误态 -->
      <div v-if="error" class="mt-4 text-center">
        <p class="text-xs text-error mb-2">{{ error }}</p>
        <AppButton variant="secondary" size="sm" @click="store.fetchAll()">重试</AppButton>
      </div>

      <!-- 分页 -->
      <div class="flex justify-center gap-1.5 mt-4">
        <button class="min-w-8 h-8 px-2.5 rounded-lg text-[13px] text-slate border border-[#e5e3df]
                       bg-white flex items-center justify-center hover:border-primary hover:text-primary">‹</button>
        <button class="min-w-8 h-8 px-2.5 rounded-lg text-[13px] bg-primary text-white border
                       border-primary font-semibold flex items-center justify-center">1</button>
        <button class="min-w-8 h-8 px-2.5 rounded-lg text-[13px] text-slate border border-[#e5e3df]
                       bg-white flex items-center justify-center hover:border-primary hover:text-primary">2</button>
        <button class="min-w-8 h-8 px-2.5 rounded-lg text-[13px] text-slate border border-[#e5e3df]
                       bg-white flex items-center justify-center hover:border-primary hover:text-primary">›</button>
      </div>
    </div>
  </div>

  <!-- 新增错题本弹窗 -->
  <div v-if="showNewCat" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30" @click="showNewCat = false" />
    <div class="relative bg-white rounded-[16px] shadow-xl w-full max-w-[400px]">
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#e5e3df]">
        <b class="text-sm text-charcoal">新增错题本</b>
        <button class="text-slate hover:text-charcoal text-lg leading-none" @click="showNewCat = false">×</button>
      </div>
      <div class="p-5">
        <label class="block">
          <span class="text-xs font-semibold text-slate mb-1 block">错题本名称</span>
          <input v-model="newCatName" placeholder="如:圆锥曲线专项 / 高考易错点…"
                 class="w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary"
                 @keyup.enter="confirmNewCat" />
        </label>
      </div>
      <div class="flex justify-end gap-2 px-5 py-4 border-t border-[#e5e3df] bg-[#fafaf9] rounded-b-[16px]">
        <AppButton variant="secondary" size="sm" @click="showNewCat = false">取消</AppButton>
        <AppButton variant="primary" size="sm" @click="confirmNewCat">创建</AppButton>
      </div>
    </div>
  </div>
</template>
