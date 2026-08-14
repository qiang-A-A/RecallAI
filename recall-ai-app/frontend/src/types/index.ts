/** Recall AI 前端类型定义(与后端 Pydantic schemas 对应)。 */

export interface QuestionKP {
  kp_id: number
  name: string
  is_primary: boolean
  confidence: number
}

export interface Question {
  id: number
  subject: string
  chapter: string
  q_type: string
  difficulty: string
  content_json: { text: string; formulas: string[]; source_type?: string }
  answer: string
  wrong_answer: string
  wrong_reason: string
  ocr_status: string
  error_count: number
  created_at: string
  kps?: QuestionKP[]
  mastery?: number
  review_count?: number
  ai_summary?: string
}

/** 录入错题请求(与后端 QuestionCreate 对应) */
export interface QuestionCreate {
  subject: string
  text: string
  answer: string
  wrong_answer: string
  wrong_reason: string
  source_type: 'text' | 'camera' | 'screenshot' | 'chat'
  image_base64?: string
}

/** AI 归档分析结果(四通道录入共用) */
export interface AIAnalyzeResult {
  ok: boolean
  subject?: string
  q_type?: string
  difficulty?: string
  kp_name?: string
  answer?: string
  wrong_reason?: string
  reason?: string
  detail?: string
}

/** OCR 识别结果 */
export interface OCRResult {
  text: string
  confidence: number
  status: string
  detail?: string
}

export interface ReviewSubmit {
  status: 'mastered' | 'fuzzy' | 'failed'
  wrong_reason: string
  hint_level: number
  time_cost_sec: number
}

export interface ReviewSubmitOut {
  next_review_at: string
  trigger_variant: boolean
  variant_task_id: string | null
}

export interface AIChatRequest {
  message: string
  question_id?: number
}

export interface AIChatResponse {
  reply: string
  sources: string[]
}

export interface WeeklyReport {
  total_questions: number
  review_count: number
  mastery_avg: number
  error_reasons: { reason: string; count: number }[]
  trend: { date: string; count: number }[]
  weak_kps: { kp_id: number; name: string; mastery: number; error_count: number }[]
  suggestions: string[]
}

export interface ChatMessage {
  role: 'user' | 'ai'
  text: string
}
