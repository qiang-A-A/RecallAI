/** Axios 封装:统一 baseURL、错误拦截 + 离线演示模式。 */
import axios from 'axios'
import type {
  AIChatRequest, AIChatResponse, AIAnalyzeResult, OCRResult, Question, QuestionConfirm, QuestionCreate,
  ReviewSubmit, ReviewSubmitOut, WeeklyReport,
} from '@/types'

const http = axios.create({
  baseURL: '/api/v1',
  timeout: 30_000,
})

// 统一错误处理:非 2xx 抛出自定义消息
http.interceptors.response.use(
  (resp) => resp,
  (err) => {
    const detail = err.response?.data?.detail ?? err.message
    return Promise.reject(new Error(detail))
  },
)

// ============================================================
// 离线演示模式:VITE_OFFLINE=true 构建(Vite define 注入)时,
// API 直接返回内置模拟数据,静态 HTML 无需后端即可完整交互。
// ============================================================
declare const __OFFLINE__: boolean
const OFFLINE = typeof __OFFLINE__ !== 'undefined' ? __OFFLINE__ : false
const delay = (ms = 300) => new Promise((r) => setTimeout(r, ms))

const MOCK_QUESTIONS: Question[] = [
  { id: 1, subject: '数学', chapter: '导数', q_type: 'solve', difficulty: 'mid', content_json: { text: '已知函数 f(x)=x³−3x²+1,求 f(x) 的单调递减区间。', formulas: [], source_type: 'text' }, answer: '(0,2)', wrong_answer: '(-∞,0)', wrong_reason: '概念混淆', ocr_status: 'processed', error_count: 3, created_at: '2026-08-10T09:00:00', kps: [{ kp_id: 1, name: '导数与单调性', is_primary: true, confidence: 0.82 }], mastery: 0.35, review_count: 3 },
  { id: 2, subject: '物理', chapter: '运动学', q_type: 'solve', difficulty: 'easy', content_json: { text: '物体从 20m 高处自由下落(g=10m/s²),求落地速度。', formulas: ['v²=2gh'], source_type: 'camera' }, answer: '20m/s', wrong_answer: '14m/s', wrong_reason: '公式误用', ocr_status: 'processed', error_count: 1, created_at: '2026-08-11T14:30:00', kps: [{ kp_id: 2, name: '自由落体运动', is_primary: true, confidence: 0.9 }], mastery: 0.6, review_count: 1 },
  { id: 3, subject: '化学', chapter: '物质的量', q_type: 'calc', difficulty: 'hard', content_json: { text: '2 mol 氢气与 1 mol 氧气完全反应,生成水的物质的量是多少?', formulas: [], source_type: 'text' }, answer: '2 mol', wrong_answer: '1 mol', wrong_reason: '审题偏差', ocr_status: 'processed', error_count: 2, created_at: '2026-08-12T10:15:00', kps: [{ kp_id: 3, name: '化学反应计量', is_primary: true, confidence: 0.78 }], mastery: 0.5, review_count: 2 },
  { id: 4, subject: '英语', chapter: '时态', q_type: 'choice', difficulty: 'easy', content_json: { text: 'By the time you arrive, I ___ for two hours.', formulas: [], source_type: 'chat' }, answer: 'will have been waiting', wrong_answer: 'will wait', wrong_reason: '方法不熟', ocr_status: 'processed', error_count: 1, created_at: '2026-08-13T08:00:00', kps: [{ kp_id: 4, name: '将来完成进行时', is_primary: true, confidence: 0.85 }], mastery: 0.45, review_count: 1 },
  { id: 5, subject: '数学', chapter: '圆锥曲线', q_type: 'solve', difficulty: 'hard', content_json: { text: '求椭圆 x²/16 + y²/9 = 1 的焦点坐标。', formulas: [], source_type: 'text' }, answer: '(±√7, 0)', wrong_answer: '(±5, 0)', wrong_reason: '概念混淆', ocr_status: 'processed', error_count: 4, created_at: '2026-08-08T16:40:00', kps: [{ kp_id: 5, name: '椭圆定义与性质', is_primary: true, confidence: 0.7 }], mastery: 0.2, review_count: 4 },
]

const MOCK_WEEKLY: WeeklyReport = {
  total_questions: 5,
  review_count: 11,
  mastery_avg: 42.0,
  error_reasons: [
    { reason: '概念混淆', count: 3 },
    { reason: '审题偏差', count: 2 },
    { reason: '公式误用', count: 1 },
    { reason: '计算失误', count: 1 },
  ],
  trend: [
    { date: '2026-08-06', count: 0 },
    { date: '2026-08-07', count: 1 },
    { date: '2026-08-08', count: 2 },
    { date: '2026-08-09', count: 1 },
    { date: '2026-08-10', count: 2 },
    { date: '2026-08-11', count: 3 },
    { date: '2026-08-12', count: 2 },
  ],
  weak_kps: [
    { kp_id: 5, name: '椭圆定义与性质', mastery: 0.2, error_count: 4 },
    { kp_id: 1, name: '导数与单调性', mastery: 0.35, error_count: 3 },
  ],
  suggestions: ['整体掌握度偏低,建议增加每日复习量并优先强化薄弱考点。', '本周最高频错因是「概念混淆」,建议针对性训练。'],
}

const MOCK_CHAT = '已收到你的问题。作为 Recall AI 学习助手,我可以按"考点提示 → 思路引导 → 完整解析"的方式帮你梳理。\n\n当前未配置 DeepSeek Key,回答由本地知识引导;配置 Key 后即可获得真实 AI 流式回答。'

/** 错题 API */
export const questionApi = {
  list: async (params?: { subject?: string; keyword?: string; page?: number }) => {
    if (OFFLINE) { await delay(); let r = MOCK_QUESTIONS; if (params?.subject && params.subject !== 'all') r = r.filter((q) => q.subject === params.subject); return r }
    return http.get<Question[]>('/questions', { params }).then((r) => r.data)
  },
  create: async (payload: QuestionCreate) => {
    if (OFFLINE) { await delay(600); const q: Question = { id: Date.now(), subject: payload.subject, chapter: '', q_type: 'solve', difficulty: 'mid', content_json: { text: payload.text, formulas: [], source_type: payload.source_type }, answer: payload.answer, wrong_answer: payload.wrong_answer, wrong_reason: payload.wrong_reason, ocr_status: 'processed', error_count: 1, created_at: new Date().toISOString(), kps: [{ kp_id: 0, name: '待确认', is_primary: true, confidence: 0.5 }], mastery: 0, review_count: 0 }; return q }
    return http.post<Question>('/questions', payload).then((r) => r.data)
  },
  get: (id: number) => OFFLINE ? Promise.resolve(MOCK_QUESTIONS.find((q) => q.id === id) as Question) : http.get<Question>(`/questions/${id}`).then((r) => r.data),
  confirm: (id: number, payload: QuestionConfirm) => OFFLINE ? Promise.resolve(MOCK_QUESTIONS[0]) : http.post<Question>(`/questions/${id}/confirm`, payload).then((r) => r.data),
  remove: (id: number) => OFFLINE ? Promise.resolve() : http.delete(`/questions/${id}`),
  exportPdf: async (subject?: string) => {
    if (OFFLINE) {
      await delay(500)
      // 离线模式:生成模拟导出内容(避免 file:// 下真实请求被 CORS 拦截)
      const content = 'Recall AI - 错题报告\n\n当前为静态演示版,导出由模拟数据生成。配置后端后可导出真实错题 PDF。'
      return new Blob([content], { type: 'application/pdf' }) as Blob
    }
    return http.get<Blob>('/questions/export/pdf', { params: { subject }, responseType: 'blob' }).then((r) => r.data)
  },
  /** 用户主动标记掌握度 */
  setMastery: (id: number, status: 'mastered' | 'fuzzy' | 'failed') => {
    if (OFFLINE) {
      // 离线版:本地更新 master_state(模拟,不持久化)
      const q = MOCK_QUESTIONS.find((x) => x.id === id)
      if (q) {
        const base = { mastered: 0.85, fuzzy: 0.5, failed: 0.2 }[status]
        q.mastery = base
      }
      return Promise.resolve(MOCK_QUESTIONS.find((x) => x.id === id) as Question)
    }
    return http.post<Question>(`/questions/${id}/mastery`, { status }).then((r) => r.data)
  },
  /** 拍照/截图图片 OCR 识别(静态版:优先尝试本地后端真实 OCR,不可用再降级) */
  ocr: async (file: File) => {
    if (OFFLINE) {
      // 先尝试本地后端(localhost:8000)真实 OCR——后端已内置 RapidOCR,file:// 下 fetch 会被 CORS 拦,但运行版可用
      try {
        const fd = new FormData()
        fd.append('file', file)
        const resp = await fetch('http://localhost:8000/api/v1/questions/ocr', { method: 'POST', body: fd })
        if (resp.ok) {
          const r = (await resp.json()) as OCRResult
          if (r.text) return r
        }
      } catch { /* 后端未启动/跨域拦截,走降级 */ }
      // 降级:提示手动录入(不再伪装成 OCR 结果)
      await delay(400)
      return { text: '', confidence: 0, status: 'need_manual' } as OCRResult
    }
    const fd = new FormData()
    fd.append('file', file)
    return http.post<OCRResult>('/questions/ocr', fd).then((r) => r.data)
  },
  /** AI 自动识别:学科 / 知识点 / 错因(离线版直连 DeepSeek) */
  analyze: async (payload: QuestionCreate) => {
    if (OFFLINE) {
      const { analyzeDirect } = await import('./deepseek-direct')
      return analyzeDirect(payload.text, payload.source_type) as AIAnalyzeResult
    }
    return http.post<AIAnalyzeResult>('/questions/analyze', payload).then((r) => r.data)
  },
}

/** 复习 API */
export const reviewApi = {
  today: async () => {
    if (OFFLINE) { await delay(400); return { count: 2, items: MOCK_QUESTIONS.slice(0, 2).map((q) => ({ question_id: q.id, due_date: '2026-08-13', status: 'fuzzy', interval_days: 1, content_text: q.content_json.text, subject: q.subject })) } }
    return http.get<{ count: number; items: unknown[] }>('/reviews/today').then((r) => r.data)
  },
  submit: async (id: number, payload: ReviewSubmit) => {
    if (OFFLINE) { await delay(600); return { next_review_at: '2026-08-15', trigger_variant: payload.status === 'failed', variant_task_id: payload.status === 'failed' ? 'vt_demo' : null } as ReviewSubmitOut }
    return http.post<ReviewSubmitOut>(`/reviews/${id}/submit`, payload).then((r) => r.data)
  },
}

/** AI API(离线/静态版直连 DeepSeek,使用用户配置的 Key) */
export const aiApi = {
  chat: async (payload: AIChatRequest) => {
    if (OFFLINE) {
      const { chatDirect } = await import('./deepseek-direct')
      try {
        const reply = await chatDirect(payload.message)
        return { reply, sources: [] } as AIChatResponse
      } catch (e) {
        return { reply: `出错了:${(e as Error).message}`, sources: [] } as AIChatResponse
      }
    }
    return http.post<AIChatResponse>('/ai/chat', payload).then((r) => r.data)
  },
  generateVariant: (payload: { kp_id?: number; question_id?: number; difficulty?: string }) =>
    OFFLINE ? Promise.resolve({ task_id: 'vt_demo', questions: [] }) : http.post<{ task_id: string; questions: unknown[] }>('/ai/variant/generate', payload).then((r) => r.data),
}

/** 分析 API */
export const analyticsApi = {
  weekly: async () => { if (OFFLINE) { await delay(400); return MOCK_WEEKLY } return http.get<WeeklyReport>('/analytics/weekly').then((r) => r.data) },
}

/** 设置 API(API Key 管理;离线版存 localStorage,直连 DeepSeek) */
export const settingsApi = {
  getStatus: async () => {
    if (OFFLINE) {
      const { getApiKey } = await import('./deepseek-direct')
      return { provider: 'DeepSeek', model: 'deepseek-chat', base_url: 'https://api.deepseek.com', api_key_configured: !!getApiKey() }
    }
    return http.get<{ provider: string; model: string; base_url: string; api_key_configured: boolean }>('/settings/ai').then((r) => r.data)
  },
  setKey: async (api_key: string) => {
    if (OFFLINE) {
      const { setApiKey } = await import('./deepseek-direct')
      setApiKey(api_key)
      return { provider: 'DeepSeek', model: 'deepseek-chat', base_url: 'https://api.deepseek.com', api_key_configured: true }
    }
    return http.post<{ provider: string; model: string; base_url: string; api_key_configured: boolean }>('/settings/api-key', { api_key }).then((r) => r.data)
  },
  clearKey: async () => {
    if (OFFLINE) {
      const { clearApiKey } = await import('./deepseek-direct')
      clearApiKey()
      return { provider: 'DeepSeek', model: 'deepseek-chat', base_url: 'https://api.deepseek.com', api_key_configured: false }
    }
    return http.delete<{ provider: string; model: string; base_url: string; api_key_configured: boolean }>('/settings/api-key').then((r) => r.data)
  },
  test: async () => {
    if (OFFLINE) {
      const { pingDirect } = await import('./deepseek-direct')
      return pingDirect()
    }
    return http.post<{ ok: boolean; message: string }>('/settings/test').then((r) => r.data)
  },
}
