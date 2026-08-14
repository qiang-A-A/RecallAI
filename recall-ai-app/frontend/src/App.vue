<script setup lang="ts">
/** 应用根组件:顶导航 + 路由视图 + 全局 Toast + 悬浮操作 + 真实业务弹窗。 */
import { ref, onMounted } from 'vue'
import { RouterView } from 'vue-router'
import TopNav from '@/components/layout/TopNav.vue'
import AppToast from '@/components/ui/AppToast.vue'
import AppButton from '@/components/ui/AppButton.vue'
import { useQuestionStore, useChatStore } from '@/stores'
import { questionApi, reviewApi } from '@/api/client'
import type { Question, QuestionCreate } from '@/types'

const store = useQuestionStore()
const chat = useChatStore()

const toastMsg = ref('')
const toastShow = ref(false)
function toast(msg: string) {
  toastMsg.value = msg
  toastShow.value = true
  setTimeout(() => (toastShow.value = false), 2200)
}

// ---------- 录入弹窗(拍照/截图/文本/对话) ----------
const showAdd = ref(false)
const addTab = ref<'camera' | 'screenshot' | 'text' | 'chat'>('text')
const addForm = ref<QuestionCreate>({
  subject: '数学', text: '', answer: '', wrong_answer: '', wrong_reason: '', source_type: 'text',
})
const addBusy = ref(false)
const aiAnalyzing = ref(false)
const aiResult = ref<{ subject?: string; kp_name?: string; wrong_reason?: string; answer?: string; reason?: string } | null>(null)
const previewImg = ref('') // 拍照/截图预览(base64)
const ocrBusy = ref(false)

const addTabs = [
  { key: 'text', label: '文本' },
  { key: 'camera', label: '拍照' },
  { key: 'screenshot', label: '截图' },
  { key: 'chat', label: '对话' },
] as const

function openAdd() {
  addTab.value = 'text'
  addForm.value = { subject: '数学', text: '', answer: '', wrong_answer: '', wrong_reason: '', source_type: 'text' }
  aiResult.value = null
  previewImg.value = ''
  showAdd.value = true
}

/** 切换录入通道:更新 source_type */
function switchTab(t: (typeof addTabs)[number]['key']) {
  addTab.value = t
  addForm.value.source_type = t === 'text' ? 'text' : t === 'chat' ? 'chat' : t === 'camera' ? 'camera' : 'screenshot'
}

/** 拍照/截图:选择图片 → OCR 识别 */
async function onPickImage(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  // 预览
  const reader = new FileReader()
  reader.onload = async () => {
    previewImg.value = String(reader.result)
    addForm.value.image_base64 = String(reader.result)
  }
  reader.readAsDataURL(file)
  // OCR
  ocrBusy.value = true
  try {
    const r = await questionApi.ocr(file)
    if (r.text && r.status !== 'need_manual') {
      addForm.value.text = r.text
      toast(`OCR 识别完成(置信度 ${Math.round(r.confidence * 100)}%)`)
      await runAI()
    } else if (r.status === 'need_manual') {
      // OCR 服务未启用(静态版场景):不写入题干,避免提示文字被当作题干做 AI 识别
      addForm.value.text = ''
      toast('图片已上传,但 OCR 未启用,请手动输入题干')
    } else if (r.status === 'unavailable') {
      addForm.value.text = ''
      toast('OCR 服务不可用,可手动补充题干')
    } else {
      addForm.value.text = ''
      toast('未识别到文字,请手动输入题干')
    }
  } catch (err) {
    toast(`OCR 失败:${(err as Error).message}`)
  } finally {
    ocrBusy.value = false
    input.value = ''
  }
}

/** 对话通道:发送一句话,由 AI 生成结构化错题 */
const chatDraft = ref('')
async function sendChatDraft() {
  const v = chatDraft.value.trim()
  if (!v) return
  addForm.value.text = v
  chatDraft.value = ''
  await runAI()
}

/** AI 自动识别:学科 / 知识点 / 错因 / 答案(四通道共用) */
async function runAI() {
  const text = addForm.value.text.trim()
  if (!text) return
  // 排除 OCR 提示文字等"非真实题干"
  if (text.length < 6 || /图片已上传|OCR 服务未启用|无法识别题目内容/.test(text)) {
    aiResult.value = null
    toast('请先填写题干内容(当前为 OCR 提示或占位文本)')
    return
  }
  aiAnalyzing.value = true
  aiResult.value = null
  try {
    const r = await questionApi.analyze({ ...addForm.value })
    if (r.ok) {
      aiResult.value = {
        subject: r.subject, kp_name: r.kp_name, wrong_reason: r.wrong_reason, answer: r.answer, reason: r.reason,
      }
      // 自动回填到表单
      if (r.subject) addForm.value.subject = r.subject
      if (r.answer) addForm.value.answer = r.answer
      if (r.wrong_reason) addForm.value.wrong_reason = r.wrong_reason
    } else {
      aiResult.value = null
      toast(`AI 识别暂不可用:${r.detail || '未配置 Key'}(可手动填写)`)
    }
  } catch (e) {
    aiResult.value = null
    toast(`AI 识别失败:${(e as Error).message}`)
  } finally {
    aiAnalyzing.value = false
  }
}

async function submitAdd() {
  if (!addForm.value.text.trim()) { toast('请填写题干'); return }
  addBusy.value = true
  try {
    const q = await store.create({ ...addForm.value })
    toast(`录入成功 #${q.id}`)
    showAdd.value = false
  } catch (e) {
    toast(`录入失败:${(e as Error).message}`)
  } finally {
    addBusy.value = false
  }
}

// ---------- 详情弹窗 ----------
const showDetail = ref(false)
const detailQ = ref<Question | null>(null)
function openDetail(q: Question) {
  detailQ.value = q
  showDetail.value = true
}

// ---------- 编辑错题 ----------
const showEdit = ref(false)
const editQ = ref<Question | null>(null)
const editForm = ref({ subject: '', text: '', answer: '', wrong_answer: '', wrong_reason: '', difficulty: '' })
const editSaving = ref(false)
function openEdit(q: Question) {
  editQ.value = q
  editForm.value = {
    subject: q.subject,
    text: q.content_json.text,
    answer: q.answer,
    wrong_answer: q.wrong_answer,
    wrong_reason: q.wrong_reason,
    difficulty: q.difficulty,
  }
  showEdit.value = true
}
async function saveEdit() {
  if (!editQ.value) return
  if (!editForm.value.text.trim()) { toast('题干不能为空'); return }
  editSaving.value = true
  try {
    await store.update(editQ.value.id, {
      subject: editForm.value.subject,
      text: editForm.value.text,
      answer: editForm.value.answer,
      wrong_answer: editForm.value.wrong_answer,
      wrong_reason: editForm.value.wrong_reason,
      difficulty: editForm.value.difficulty,
    })
    // 若详情/编辑的是同一题,同步详情内容
    if (detailQ.value?.id === editQ.value.id) detailQ.value = store.items.find((x) => x.id === editQ.value!.id) ?? null
    toast('已保存修改')
    showEdit.value = false
  } catch (e) {
    toast(`保存失败:${(e as Error).message}`)
  } finally {
    editSaving.value = false
  }
}

// ---------- 删除 ----------
async function onRemove(q: Question) {
  if (!confirm(`确定删除这道错题吗?\n${q.content_json.text.slice(0, 30)}…`)) return
  try {
    await store.remove(q.id)
    if (detailQ.value?.id === q.id) showDetail.value = false
    toast('已删除')
  } catch (e) {
    toast(`删除失败:${(e as Error).message}`)
  }
}

// ---------- 一键复习弹窗 ----------
const showReview = ref(false)
const reviewItems = ref<{ id: number; text: string; subject: string }[]>([])
const reviewBusy = ref(false)
async function openReview() {
  showReview.value = true
  reviewBusy.value = true
  reviewItems.value = []
  try {
    const data = await reviewApi.today()
    reviewItems.value = (data.items as unknown[]).map((it: Record<string, unknown>) => ({
      id: it.question_id as number,
      text: (it.content_text as string) || '未命名题目',
      subject: (it.subject as string) || '',
    }))
    if (!reviewItems.value.length) toast('今天没有待复习的题目 🎉')
  } catch (e) {
    toast(`获取复习列表失败:${(e as Error).message}`)
  } finally {
    reviewBusy.value = false
  }
}
async function submitReview(q: { id: number; text: string }, status: 'mastered' | 'fuzzy' | 'failed') {
  try {
    const r = await reviewApi.submit(q.id, { status, wrong_reason: '', hint_level: 0, time_cost_sec: 0 })
    toast(`已提交,下次复习 ${r.next_review_at}`)
    reviewItems.value = reviewItems.value.filter((x) => x.id !== q.id)
    // 立即同步:错题集 + 看板即时反映复习后的掌握度(不等 fetchAll 网络往返)
    store.applyReview(q.id, status)
    await store.fetchAll()
  } catch (e) {
    toast(`提交失败:${(e as Error).message}`)
  }
}

// ---------- 导出 ----------
async function onExport() {
  try {
    const blob = await questionApi.exportPdf()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'recall-report.pdf'
    a.click()
    URL.revokeObjectURL(url)
    toast('导出成功')
  } catch (e) {
    toast(`导出失败:${(e as Error).message}`)
  }
}

onMounted(() => { void store.fetchAll() })
</script>

<template>
  <TopNav />
  <main class="max-w-[1180px] mx-auto px-4 md:px-6 py-6 pb-24">
    <RouterView
      @record="openAdd"
      @review="openReview"
      @export="onExport"
      @remove="onRemove"
      @detail="openDetail"
      @edit="openEdit"
    />
  </main>

  <!-- 悬浮操作(FAB) -->
  <div class="fixed right-6 bottom-6 z-[80] flex flex-col gap-2.5">
    <button aria-label="录入错题" class="w-[50px] h-[50px] rounded-[15px] bg-link text-white
               shadow-lg flex items-center justify-center transition-transform
               hover:scale-105 active:scale-95" @click="openAdd">
      <svg viewBox="0 0 24 24" class="w-5 h-5" fill="none" stroke="currentColor"
           stroke-width="2" stroke-linecap="round"><path d="M12 5v14M5 12h14" /></svg>
    </button>
    <button aria-label="开始复习" class="w-[50px] h-[50px] rounded-[15px] text-white
               bg-gradient-to-br from-ai-start to-ai-end shadow-lg flex items-center
               justify-center transition-transform hover:scale-105 active:scale-95"
            @click="openReview">
      <svg viewBox="0 0 24 24" class="w-5 h-5" fill="currentColor"><path d="M5 3l14 9-14 9z" /></svg>
    </button>
  </div>

  <!-- 录入错题弹窗(四通道) -->
  <div v-if="showAdd" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30" @click="showAdd = false" />
    <div class="relative bg-white rounded-[16px] shadow-xl w-full max-w-[560px] max-h-[90vh] overflow-y-auto">
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#e5e3df]">
        <b class="text-sm text-charcoal">录入错题</b>
        <button class="text-slate hover:text-charcoal text-lg leading-none" @click="showAdd = false">×</button>
      </div>

      <!-- 四通道 Tab -->
      <div class="flex gap-1 px-5 pt-3.5">
        <button v-for="t in addTabs" :key="t.key"
                class="flex-1 py-2 rounded-lg text-[13px] font-semibold transition-all"
                :class="addTab === t.key
                  ? 'bg-tint-lavender text-primary-deep'
                  : 'text-slate hover:bg-[#f6f5f4]'"
                @click="switchTab(t.key)">
          {{ t.label }}
        </button>
      </div>

      <div class="p-5 space-y-3.5">
        <!-- 拍照通道 -->
        <div v-if="addTab === 'camera' || addTab === 'screenshot'" class="space-y-3">
          <label class="block cursor-pointer">
            <div class="border-2 border-dashed border-[#c8c4be] rounded-[12px] py-8 text-center
                        transition-all hover:border-primary hover:bg-[#fafaf9]">
              <svg viewBox="0 0 24 24" class="w-7 h-7 mx-auto mb-2 text-stone" fill="none"
                   stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z" />
                <circle cx="12" cy="13" r="4" />
              </svg>
              <p class="text-[13px] font-semibold text-charcoal mb-0.5">
                {{ addTab === 'camera' ? '拍照 / 选择图片' : '上传截图' }}
              </p>
              <p class="text-[11px] text-stone">{{ ocrBusy ? 'OCR 识别中…' : '支持 JPG / PNG,自动识别题目文字' }}</p>
            </div>
            <input type="file" accept="image/*" class="hidden" :key="addTab" @change="onPickImage" />
          </label>
          <img v-if="previewImg" :src="previewImg" class="max-h-[140px] rounded-[10px] border border-[#e5e3df] mx-auto" alt="预览" />
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">识别出的题干(可编辑)</span>
            <textarea v-model="addForm.text" rows="2"
                      class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary"
                      placeholder="OCR 识别结果将显示在这里…" />
          </label>
        </div>

        <!-- 文本通道 -->
        <div v-if="addTab === 'text'" class="space-y-3">
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">题干 <i class="text-error">*</i></span>
            <textarea v-model="addForm.text" rows="3"
                      class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary"
                      placeholder="输入题目内容,支持 LaTeX 公式…" />
          </label>
          <div class="flex items-center justify-end">
            <AppButton variant="secondary" size="sm" :disabled="aiAnalyzing || !addForm.text.trim()" @click="runAI">
              {{ aiAnalyzing ? '识别中…' : 'AI 自动识别' }}
            </AppButton>
          </div>
        </div>

        <!-- 对话通道 -->
        <div v-if="addTab === 'chat'" class="space-y-3">
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">用对话描述错题</span>
            <textarea v-model="chatDraft" rows="3"
                      class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary"
                      placeholder="例如:我有一道物理题,物体从 20 米高的楼顶自由下落,求落地速度,我算成 14 了…" />
          </label>
          <div class="flex items-center justify-end">
            <AppButton variant="primary" size="sm" :disabled="aiAnalyzing || !chatDraft.trim()" @click="sendChatDraft">
              {{ aiAnalyzing ? 'AI 整理中…' : '发送给 AI 整理' }}
            </AppButton>
          </div>
        </div>

        <!-- AI 识别结果 -->
        <div v-if="aiAnalyzing" class="flex items-center gap-2 text-xs text-primary-deep bg-tint-lavender/50 rounded-lg px-3 py-2.5">
          <svg viewBox="0 0 24 24" class="w-4 h-4 animate-spin" fill="none" stroke="currentColor"
               stroke-width="2" stroke-linecap="round"><path d="M21 12a9 9 0 1 1-6.219-8.56" /></svg>
          AI 正在识别学科、知识点、错因…
        </div>
        <div v-else-if="aiResult"
             class="border-l-[3px] border-[#6366f1] bg-[#fafaf9] rounded-r-lg px-3.5 py-3 text-[12.5px] space-y-1.5">
          <div class="flex items-center gap-2 flex-wrap">
            <span class="text-[11px] font-bold text-white bg-gradient-to-r from-ai-start to-ai-end rounded-full px-2 py-0.5">AI 识别</span>
            <b class="text-primary-deep">{{ aiResult.subject || '—' }}</b>
            <span class="text-slate">·</span>
            <span class="text-charcoal">{{ aiResult.kp_name || '知识点待确认' }}</span>
          </div>
          <p class="text-slate m-0">错因:<b class="text-charcoal">{{ aiResult.wrong_reason || '—' }}</b>
            <span v-if="aiResult.answer">· 答案:<b class="text-charcoal">{{ aiResult.answer }}</b></span>
          </p>
          <p v-if="aiResult.reason" class="text-stone m-0 text-[11.5px]">{{ aiResult.reason }}</p>
        </div>

        <!-- 公共字段 -->
        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">学科 <i class="text-[10px] not-italic text-stone">(AI 自动识别,可改)</i></span>
            <select v-model="addForm.subject"
                    class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary">
              <option>数学</option><option>物理</option><option>化学</option>
              <option>生物</option><option>英语</option><option>语文</option>
            </select>
          </label>
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">正确答案</span>
            <input v-model="addForm.answer"
                   class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary" />
          </label>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">我的错误答案</span>
            <input v-model="addForm.wrong_answer"
                   class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary" />
          </label>
          <label class="block">
            <span class="text-xs font-semibold text-slate mb-1 block">错误原因 <i class="text-[10px] not-italic text-stone">(AI 自动识别,可改)</i></span>
            <input v-model="addForm.wrong_reason" placeholder="概念混淆 / 计算失误…"
                   class="w-full border border-[#e5e3df] rounded-lg px-2.5 py-2 text-[13px] outline-none focus:border-primary" />
          </label>
        </div>
      </div>
      <div class="flex justify-end gap-2 px-5 py-4 border-t border-[#e5e3df] bg-[#fafaf9] rounded-b-[16px]">
        <AppButton variant="secondary" size="sm" @click="showAdd = false">取消</AppButton>
        <AppButton variant="primary" size="sm" :disabled="addBusy" @click="submitAdd">
          {{ addBusy ? '提交中…' : '确认录入' }}
        </AppButton>
      </div>
    </div>
  </div>

  <!-- 详情弹窗 -->
  <div v-if="showDetail && detailQ" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30" @click="showDetail = false" />
    <div class="relative bg-white rounded-[16px] shadow-xl w-full max-w-[560px] max-h-[88vh] overflow-y-auto">
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#e5e3df]">
        <b class="text-sm text-charcoal">错题详情 #{{ detailQ.id }}</b>
        <button class="text-slate hover:text-charcoal text-lg leading-none" @click="showDetail = false">×</button>
      </div>
      <div class="p-5 space-y-3 text-[13px]">
        <div class="flex gap-2">
          <span class="bg-tint-lavender text-primary-deep text-[11px] font-bold px-2 py-0.5 rounded-md">{{ detailQ.subject }}</span>
          <span class="bg-[#f6f5f4] text-stone text-[11px] font-bold px-2 py-0.5 rounded-md">{{ detailQ.ocr_status }}</span>
          <span class="bg-[#f6f5f4] text-stone text-[11px] font-bold px-2 py-0.5 rounded-md">错 {{ detailQ.error_count }} 次</span>
        </div>
        <p class="text-charcoal leading-relaxed">{{ detailQ.content_json.text }}</p>
        <div class="grid grid-cols-2 gap-2.5">
          <div class="border border-[#e5e3df] rounded-lg p-2.5">
            <span class="text-[11px] text-stone block mb-0.5">正确答案</span>
            <b class="text-success">{{ detailQ.answer || '—' }}</b>
          </div>
          <div class="border border-[#e5e3df] rounded-lg p-2.5">
            <span class="text-[11px] text-stone block mb-0.5">我的答案</span>
            <b class="text-error">{{ detailQ.wrong_answer || '—' }}</b>
          </div>
        </div>
        <div class="border-l-[3px] border-[#6366f1] bg-[#fafaf9] rounded-r-lg p-2.5">
          <b class="text-primary-deep text-xs">AI 解析</b>
          <p class="text-slate mt-1">知识点:{{ detailQ.kps?.[0]?.name || '待确认' }}<br />
            错因:{{ detailQ.wrong_reason || '—' }}</p>
        </div>
      </div>
      <div class="flex justify-end gap-2 px-5 py-4 border-t border-[#e5e3df] bg-[#fafaf9] rounded-b-[16px]">
        <AppButton variant="secondary" size="sm" @click="onRemove(detailQ)">删除</AppButton>
        <AppButton variant="primary" size="sm" @click="showDetail = false">关闭</AppButton>
      </div>
    </div>
  </div>

  <!-- 编辑错题弹窗 -->
  <div v-if="showEdit && editQ" class="fixed inset-0 z-[110] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30" @click="showEdit = false" />
    <div class="relative bg-white rounded-[16px] shadow-xl w-full max-w-[560px] overflow-hidden">
      <div class="flex items-center gap-2.5 px-5 py-3.5 border-b border-[#e5e3df]">
        <svg viewBox="0 0 24 24" class="w-4 h-4 text-primary" fill="none" stroke="currentColor"
             stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
        <b class="text-sm text-charcoal">编辑错题 #{{ editQ.id }}</b>
        <button class="ml-auto text-slate hover:text-charcoal text-lg leading-none" @click="showEdit = false">×</button>
      </div>
      <div class="p-5 space-y-3.5">
        <div class="grid grid-cols-2 gap-3">
          <label class="block">
            <span class="text-xs font-semibold text-charcoal">学科</span>
            <select v-model="editForm.subject"
                    class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary bg-white">
              <option v-for="s in ['数学','物理','化学','生物','英语','语文','其他']" :key="s" :value="s">{{ s }}</option>
            </select>
          </label>
          <label class="block">
            <span class="text-xs font-semibold text-charcoal">难度</span>
            <select v-model="editForm.difficulty"
                    class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary bg-white">
              <option value="easy">容易</option><option value="mid">中等</option><option value="hard">困难</option>
            </select>
          </label>
        </div>
        <label class="block">
          <span class="text-xs font-semibold text-charcoal">题干<span class="text-error">*</span></span>
          <textarea v-model="editForm.text" rows="3"
                    class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary resize-y"
                    placeholder="题目内容,支持 LaTeX 公式"></textarea>
        </label>
        <div class="grid grid-cols-1 gap-3">
          <label class="block">
            <span class="text-xs font-semibold text-charcoal">正确答案</span>
            <input v-model="editForm.answer" class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary" placeholder="参考答案" />
          </label>
          <label class="block">
            <span class="text-xs font-semibold text-charcoal">错误作答</span>
            <input v-model="editForm.wrong_answer" class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary" placeholder="当时的错误答案(可选)" />
          </label>
          <label class="block">
            <span class="text-xs font-semibold text-charcoal">错因</span>
            <select v-model="editForm.wrong_reason"
                    class="mt-1 w-full border border-[#e5e3df] rounded-lg px-3 py-2 text-[13px] outline-none focus:border-primary bg-white">
              <option value="">未标注</option>
              <option v-for="r in ['概念混淆','计算失误','审题偏差','方法不熟','其他']" :key="r" :value="r">{{ r }}</option>
            </select>
          </label>
        </div>
      </div>
      <div class="flex items-center gap-2.5 px-5 py-3.5 border-t border-[#e5e3df] bg-[#fafaf9]">
        <AppButton variant="secondary" size="sm" @click="showEdit = false">取消</AppButton>
        <div class="ml-auto" />
        <AppButton variant="primary" size="sm" :disabled="editSaving" @click="saveEdit">
          {{ editSaving ? '保存中…' : '保存修改' }}
        </AppButton>
      </div>
    </div>
  </div>

  <!-- 一键复习弹窗 -->
  <div v-if="showReview" class="fixed inset-0 z-[100] flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/30" @click="showReview = false" />
    <div class="relative bg-white rounded-[16px] shadow-xl w-full max-w-[520px] max-h-[88vh] overflow-y-auto">
      <div class="flex items-center justify-between px-5 py-4 border-b border-[#e5e3df]">
        <b class="text-sm text-charcoal">今日复习</b>
        <button class="text-slate hover:text-charcoal text-lg leading-none" @click="showReview = false">×</button>
      </div>
      <div class="p-5 space-y-2.5">
        <p v-if="reviewBusy" class="text-center text-xs text-stone py-8">加载中…</p>
        <p v-else-if="!reviewItems.length" class="text-center text-xs text-stone py-8">今天没有待复习的题目 🎉</p>
        <div v-for="it in reviewItems" :key="it.id"
             class="border border-[#e5e3df] rounded-[12px] p-3">
          <div class="flex items-center gap-1.5 mb-1.5">
            <span class="text-[11px] font-bold bg-tint-lavender text-primary-deep px-2 py-0.5 rounded-md">{{ it.subject || '题目' }}</span>
          </div>
          <p class="text-[13px] text-charcoal leading-relaxed mb-2.5 line-clamp-2">{{ it.text }}</p>
          <div class="flex gap-1.5">
            <button class="text-[12px] px-2.5 py-1 rounded-lg bg-success/10 text-[#0a6b1f] font-semibold
                           hover:bg-success/20" @click="submitReview(it, 'mastered')">已掌握</button>
            <button class="text-[12px] px-2.5 py-1 rounded-lg bg-warning/10 text-[#9c3f00] font-semibold
                           hover:bg-warning/20" @click="submitReview(it, 'fuzzy')">模糊</button>
            <button class="text-[12px] px-2.5 py-1 rounded-lg bg-error/10 text-error font-semibold
                           hover:bg-error/20" @click="submitReview(it, 'failed')">不会</button>
          </div>
        </div>
      </div>
    </div>
  </div>

  <AppToast :message="toastMsg" :show="toastShow" />
</template>
