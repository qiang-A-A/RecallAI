<script setup lang="ts">
/** 数据看板页:KPI + 环形占比 + 最近十天 + 错因 TOP5 + AI 推荐。 */
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { storeToRefs } from 'pinia'
import { analyticsApi, questionApi } from '@/api/client'
import { useQuestionStore } from '@/stores'
import type { WeeklyReport, Question } from '@/types'
import AppBadge from '@/components/ui/AppBadge.vue'

const router = useRouter()
const store = useQuestionStore()
// 监听错题列表刷新信号(标记掌握度/录入/删除/复习等),看板自动重算
const { refreshTick } = storeToRefs(store)
const report = ref<WeeklyReport | null>(null)
const loading = ref(true)
const allQuestions = ref<Question[]>([])
const range = ref('30') // 时间范围:7/30/90
const subjectFilter = ref('all')

// ---------- 数据加载 ----------
async function loadData() {
  loading.value = true
  try {
    const [rep, qs] = await Promise.all([
      analyticsApi.weekly(),
      questionApi.list(),
    ])
    report.value = rep
    allQuestions.value = qs
  } catch {
    // 后端未启动时静默,前端演示数据兜底
  } finally {
    loading.value = false
  }
}

// ---------- KPI(从 store.items 实时计算,确保用户操作后立即变化) ----------
const kpis = computed(() => {
  const items = store.items
  const total = items.length
  // 平均掌握度:按 mastery 直接平均
  const avgMastery = total
    ? items.reduce((s, q) => s + (q.mastery ?? 0), 0) / total
    : 0
  // 本周活跃度:所有题 review_count 之和(覆盖标记 + 复习)
  const reviewCount = items.reduce((s, q) => s + (q.review_count ?? 0), 0)
  // 薄弱考点:mastery < 0.5 的题按学科聚合
  const subjWeak = new Map<string, { count: number; avg: number; sum: number }>()
  for (const q of items) {
    if ((q.mastery ?? 0) < 0.5) {
      const e = subjWeak.get(q.subject) ?? { count: 0, avg: 0, sum: 0 }
      e.count++
      e.sum += q.mastery ?? 0
      e.avg = e.sum / e.count
      subjWeak.set(q.subject, e)
    }
  }
  return [
    { label: '题目总数', value: String(total), unit: '道', delta: '实时在库', up: true },
    { label: '本周复习', value: String(reviewCount), unit: '次', delta: '标记+复习', up: true },
    { label: '平均掌握度', value: String(Math.round(avgMastery * 100)), unit: '%', delta: '按 mastery 实时', up: avgMastery >= 0.6 },
    { label: '薄弱考点', value: String(subjWeak.size), unit: '个', delta: 'mastery<50%', up: false },
  ]
})

// ---------- 环形占比(实时从 store.items 算) ----------
const donut = computed(() => {
  const items = store.items
  let mastered = 0, fuzzy = 0, failed = 0
  for (const q of items) {
    const m = q.mastery ?? 0
    if (m >= 0.7) mastered++
    else if (m >= 0.4) fuzzy++
    else failed++
  }
  const total = items.length || 1
  const pct = (n: number) => Math.round((n / total) * 100)
  const mm = pct(mastered), ff = pct(fuzzy), ff2 = 100 - mm - ff
  return [
    { label: '已掌握', value: mm, color: '#1aae39' },
    { label: '模糊', value: ff, color: '#dd5b00' },
    { label: '不会', value: Math.max(0, ff2), color: '#e03131' }
  ]
})
const centerPct = computed(() => donut.value[0].value)

// ---------- 错因分布 TOP5(实时基于 store.items 统计当前错因) ----------
const errorReasons = computed(() => {
  const counter = new Map<string, number>()
  for (const q of store.items) {
    const r = (q.wrong_reason || '').trim() || '未标记'
    counter.set(r, (counter.get(r) ?? 0) + 1)
  }
  return Array.from(counter.entries())
    .map(([reason, count]) => ({ reason, count }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 5)
})

// ---------- 最近十天(从 trend 取最近 10 天) ----------
const days = computed(() => {
  const tr = report.value?.trend ?? []
  const last = tr.slice(-10)
  const max = Math.max(1, ...last.map((d) => d.count))
  return last.map((d) => ({
    d: d.date.slice(5).replace('-', '/'),
    v: d.count,
    w: Math.max(8, Math.round((d.count / max) * 100)),
    low: d.count === 0,
  }))
})

// ---------- AI 推荐(动态,从实时 items 计算) ----------
const aiRecs = computed(() => {
  const recs: { tag: string; tagV: 'warn' | 'sys'; title: string; desc: string; actions: string[]; prompt: string }[] = []
  // 薄弱考点(按学科 mastery 平均 < 0.5)
  const subjMap = new Map<string, { count: number; sum: number; failed: number }>()
  for (const q of store.items) {
    const e = subjMap.get(q.subject) ?? { count: 0, sum: 0, failed: 0 }
    e.count++
    e.sum += q.mastery ?? 0
    if ((q.mastery ?? 0) < 0.5) e.failed++
    subjMap.set(q.subject, e)
  }
  const weak = Array.from(subjMap.entries())
    .map(([name, e]) => ({ name, count: e.count, mastery: e.sum / e.count, error_count: e.failed }))
    .filter((x) => x.mastery < 0.5 && x.count >= 1)
    .sort((a, b) => a.mastery - b.mastery)
  if (weak.length) {
    for (const k of weak.slice(0, 3)) {
      recs.push({
        tag: '薄弱考点', tagV: 'warn' as const,
        title: `${k.name}`, desc: `掌握度 ${Math.round(k.mastery * 100)}%,累计错 ${k.error_count} 次,建议强化训练。`,
        actions: ['开始强化', '查看讲解'],
        prompt: `我最近在「${k.name}」这个知识点上掌握度不高,请帮我讲解核心方法并出几道训练题。`,
      })
    }
  }
  const sug = report.value?.suggestions ?? []
  if (sug.length) {
    for (const s of sug.slice(0, 2)) {
      recs.push({
        tag: '学习建议', tagV: 'sys' as const,
        title: s.slice(0, 18), desc: s,
        actions: ['去复习', '生成计划'],
        prompt: `根据我的学习情况「${s}」,帮我安排今天的复习计划。`,
      })
    }
  }
  return recs
})

/** AI 推荐按钮动作:跳转 AI 答疑并携带上下文提问 */
function runAction(r: { prompt: string; actions: string[] }, action: string) {
  if (action === '稍后提醒') {
    showTip('已设置稍后提醒,晚些时候再安排复习')
    return
  }
  if (action === '去复习' || action === '立即复习') {
    router.push({ name: 'questions' })
    return
  }
  router.push({ name: 'ai', query: { q: r.prompt } })
}

const tip = ref('')
function showTip(msg: string) {
  tip.value = msg
  setTimeout(() => (tip.value = ''), 2200)
}

/** 导出 PDF 报告 */
async function exportReport() {
  try {
    const blob = await questionApi.exportPdf()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'recall-report.pdf'
    a.click()
    URL.revokeObjectURL(url)
    showTip('报告导出成功')
  } catch (e) {
    showTip(`导出失败:${(e as Error).message}`)
  }
}

// ---------- 下拉交互 ----------
function applyFilter() {
  // 时间范围与学科筛选:刷新数据(演示:调 weekly + 全量列表,后续可接后端参数)
  void loadData()
  showTip(`已应用:近 ${range.value} 天 · ${subjectFilter.value === 'all' ? '全部学科' : subjectFilter.value}`)
}

// 环形图 SVG 计算
const CIRC = 2 * Math.PI * 48 // 周长

function donutSeg(value: number, offset: number): { dash: number; off: number } {
  return { dash: (value / 100) * CIRC, off: -offset }
}

/** 环形图累计偏移:前面所有分段的 dash 之和 */
function donutCumOffset(idx: number): number {
  return donut.value.slice(0, idx).reduce((acc, s) => acc + (s.value / 100) * CIRC, 0)
}

onMounted(loadData)
// 关键修复:用户标记掌握度 / 录入 / 复习后,看板自动重新拉取,实时反映行为
watch(refreshTick, () => { void loadData() })
watch([range, subjectFilter], () => { void loadData() })
</script>

<template>
  <div v-if="loading" class="grid grid-cols-4 gap-3.5">
    <div v-for="i in 4" :key="i" class="h-24 rounded-2xl bg-gradient-to-r from-[#f6f5f4]
                 via-[#ece9e4] to-[#f6f5f4] bg-[length:200%_100%] animate-pulse" />
  </div>

  <div v-else class="space-y-4">
    <!-- 筛选行 -->
    <div class="flex flex-wrap items-center gap-2 bg-white border border-[#e5e3df]
                rounded-[16px] px-4 py-3">
      <select v-model="range" @change="applyFilter" class="border border-[#c8c4be] rounded-lg px-3 py-1.5 text-xs bg-white cursor-pointer" aria-label="时间范围">
        <option value="7">近 7 天</option><option value="30">近 30 天</option><option value="90">近 90 天</option>
      </select>
      <select v-model="subjectFilter" @change="applyFilter" class="border border-[#c8c4be] rounded-lg px-3 py-1.5 text-xs bg-white cursor-pointer" aria-label="学科">
        <option value="all">学科:全部</option><option>数学</option><option>物理</option><option>化学</option><option>英语</option>
      </select>
      <button @click="exportReport" class="ml-auto flex items-center gap-1.5 text-xs font-semibold text-charcoal
                     bg-white border border-[#c8c4be] rounded-lg px-3 py-1.5 hover:border-primary hover:text-primary">
        <svg viewBox="0 0 24 24" class="w-3.5 h-3.5" fill="none" stroke="currentColor"
             stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
        </svg>
        导出报告
      </button>
    </div>

    <!-- KPI -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-3.5">
      <div v-for="k in kpis" :key="k.label"
           class="bg-white border border-[#e5e3df] rounded-[16px] p-4 shadow-xs">
        <div class="text-xs text-steel mb-1.5">{{ k.label }}</div>
        <div class="text-[26px] font-bold text-charcoal leading-tight tabular-nums">
          {{ k.value }}<small class="text-[13px] font-medium text-stone">{{ k.unit }}</small>
        </div>
        <div class="text-[11.5px] mt-1" :class="k.up ? 'text-success' : 'text-stone'">{{ k.delta }}</div>
      </div>
    </div>

    <!-- 环形 + 柱状 -->
    <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
      <!-- 完成占比 -->
      <div class="bg-white border border-[#e5e3df] rounded-[16px] p-5 shadow-xs">
        <div class="flex items-center justify-between pb-2.5 mb-3.5 border-b border-[#e5e3df]">
          <span class="text-sm font-semibold text-charcoal">完成情况占比</span>
          <span class="text-[11px] text-stone font-normal">点击分段下载错题列表</span>
        </div>
        <div class="flex items-center gap-5">
          <div class="w-[130px] h-[130px] relative flex-none">
            <svg width="130" height="130" viewBox="0 0 130 130" class="-rotate-90">
              <circle cx="65" cy="65" r="48" fill="none" stroke="#f2f2f2" stroke-width="18" />
              <circle
                v-for="(s, i) in donut"
                :key="s.label"
                cx="65" cy="65" r="48" fill="none"
                :stroke="s.color" stroke-width="18"
                :stroke-dasharray="`${donutSeg(s.value, 0).dash} 302`"
                :stroke-dashoffset="-donutCumOffset(i)"
                stroke-linecap="butt"
              />
            </svg>
            <div class="absolute inset-0 flex flex-col items-center justify-center">
              <b class="text-[22px] text-charcoal leading-none tabular-nums">{{ centerPct }}%</b>
              <span class="text-[10px] text-stone">已掌握</span>
            </div>
          </div>
          <div class="flex-1 flex flex-col gap-2">
            <div v-for="s in donut" :key="s.label"
                 class="flex items-center gap-2 text-xs">
              <span class="w-3 h-3 rounded-sm flex-none" :style="{ background: s.color }" />
              {{ s.label }}<span class="ml-auto font-bold tabular-nums">{{ s.value }}%</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 最近十天 -->
      <div class="bg-white border border-[#e5e3df] rounded-[16px] p-5 shadow-xs">
        <div class="flex items-center justify-between pb-2.5 mb-2.5 border-b border-[#e5e3df]">
          <span class="text-sm font-semibold text-charcoal">最近十天做题情况</span>
          <span class="text-[11px] text-stone font-normal">柱高 = 做题量 · 橙 = 正确率低</span>
        </div>
        <div class="flex items-end gap-1.5 h-[140px] px-1 pt-2">
          <div v-for="d in days" :key="d.d"
               class="flex-1 flex flex-col items-center gap-1 h-full justify-end">
            <span class="text-[10px] text-steel tabular-nums leading-none">{{ d.v }}</span>
            <div class="w-full max-w-[32px] rounded-t-md transition-all hover:brightness-95"
                 :class="d.low ? 'bg-tint-peach border border-warning' : 'bg-tint-lavender border border-primary'"
                 :style="{ height: d.w + '%' }" />
            <span class="text-[10px] text-stone leading-none">{{ d.d }}</span>
          </div>
        </div>
        <div class="flex justify-between text-[10px] text-stone border-t border-[#c8c4be] mx-1 pt-1">
          <span>8/3</span><span>8/6</span><span>8/9</span><span>8/12</span>
        </div>
      </div>
    </div>

      <!-- 错因 + AI 推荐 -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">      <!-- 错因 TOP5 -->
      <div class="bg-white border border-[#e5e3df] rounded-[16px] p-5 shadow-xs">
        <div class="text-sm font-semibold text-charcoal pb-2.5 mb-3.5 border-b border-[#e5e3df]">
          错因分布 TOP5
        </div>
        <div v-if="errorReasons.length" class="space-y-2.5">
          <div v-for="r in errorReasons" :key="r.reason"
               class="flex items-center gap-2.5">
            <span class="w-[70px] text-xs text-slate text-right flex-none">{{ r.reason }}</span>
            <div class="flex-1 h-[22px] bg-[#f6f5f4] rounded-md overflow-hidden">
              <div class="h-full rounded-md bg-gradient-to-r from-ai-start to-ai-end flex items-center
                          justify-end pr-2 text-[11px] font-bold text-white"
                   :style="{ width: Math.min(100, r.count * 20) + '%' }">{{ r.count }}</div>
            </div>
          </div>
        </div>
        <div v-else class="text-center py-8 text-stone text-xs">暂无错题数据</div>
      </div>

      <!-- AI 优化推荐 -->
      <div class="bg-white border border-[#e5e3df] rounded-[16px] p-5 shadow-xs">
        <div class="flex items-center justify-between pb-2.5 mb-3.5 border-b border-[#e5e3df]">
          <span class="text-sm font-semibold text-charcoal">AI 题目优化推荐</span>
          <span class="text-[11px] text-stone font-normal">基于薄弱考点自动推荐</span>
        </div>
        <div class="flex flex-col gap-2.5">
          <div v-for="r in aiRecs" :key="r.title"
               class="bg-[#fafaf9] border border-[#e5e3df] rounded-[12px] p-3.5">
            <div class="flex items-center gap-2 text-[13px] font-semibold mb-1">
              <AppBadge :variant="r.tagV">{{ r.tag }}</AppBadge>{{ r.title }}
            </div>
            <p class="text-xs text-slate mb-2.5 m-0">{{ r.desc }}</p>
            <div class="flex gap-2 flex-wrap">
              <button v-for="a in r.actions" :key="a" @click="runAction(r, a)"
                      class="text-xs px-3 py-1.5 rounded-lg font-semibold transition-all"
                      :class="a === r.actions[0]
                        ? 'bg-primary text-white hover:bg-primary-pressed'
                        : 'bg-white text-charcoal border border-[#c8c4be] hover:border-primary hover:text-primary'">
                {{ a }}
              </button>
            </div>
          </div>
          <div v-if="!aiRecs.length"
               class="bg-[#fafaf9] border border-[#e5e3df] rounded-[12px] p-3.5 text-center text-xs text-stone">
            <p class="mb-1.5">暂无薄弱考点数据</p>
            <p class="mb-2.5">录入错题并完成复习后,这里会根据你的学习画像自动推荐。</p>
            <button class="text-xs px-3 py-1.5 rounded-lg font-semibold bg-primary text-white hover:bg-primary-pressed"
                    @click="router.push({ name: 'questions' })">去录入错题</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- 轻提示 -->
  <transition name="fade">
    <div v-if="tip"
         class="fixed left-1/2 -translate-x-1/2 bottom-8 z-[120] px-4 py-2.5 rounded-xl
                bg-charcoal/90 text-white text-xs shadow-lg">
      {{ tip }}
    </div>
  </transition>
</template>
