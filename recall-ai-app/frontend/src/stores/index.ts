/** Pinia store:错题列表状态 + AI 对话状态。 */
import { defineStore } from 'pinia'
import type { ChatMessage, Question } from '@/types'
import { aiApi, questionApi } from '@/api/client'

export const useQuestionStore = defineStore('questions', {
  state: () => ({
    items: [] as Question[],
    loading: false,
    error: '' as string,
    filter: { subject: 'all' as string, keyword: '' as string },
    /** 刷新信号:被错题列表/复习/标记掌握等操作自增,AnalyticsView 监听以实时联动 */
    refreshTick: 0,
  }),
  getters: {
    filtered: (s) =>
      s.items.filter((q) => s.filter.subject === 'all' || q.subject === s.filter.subject),
  },
  actions: {
    async fetchAll() {
      this.loading = true
      this.error = ''
      try {
        this.items = await questionApi.list()
      } catch (e) {
        this.error = (e as Error).message
      } finally {
        this.loading = false
      }
    },
    async create(payload: import('@/types').QuestionCreate) {
      const q = await questionApi.create(payload)
      this.items.unshift(q)
      this.refreshTick++
      return q
    },
    async remove(id: number) {
      await questionApi.remove(id)
      this.items = this.items.filter((q) => q.id !== id)
      this.refreshTick++
    },
    /** 用户标记掌握度:更新本地 + 触发看板刷新 */
    async setMastery(id: number, status: 'mastered' | 'fuzzy' | 'failed') {
      const newMastery = { mastered: 0.85, fuzzy: 0.5, failed: 0.2 }[status]
      // 直接修改 store.items(响应式代理),Vue 会自动触发 QuestionsView/AnalyticsView 更新
      const item = this.items.find((q) => q.id === id)
      if (item) {
        item.mastery = newMastery
        // 主动标记也算一次活跃(纳入「本周复习」计数),同时让 review_count 反映学习历程
        item.review_count = (item.review_count ?? 0) + 1
      }
      this.refreshTick++
      // 运行版同步到后端(失败不阻塞 UI,store 已更新)
      try { await questionApi.setMastery(id, status) } catch { /* offline */ }
      return item
    },
    /** 其他操作后通知看板刷新 */
    bumpRefresh() { this.refreshTick++ },
  },
})

export const useChatStore = defineStore('chat', {
  state: () => ({
    messages: [] as ChatMessage[],
    typing: false,
    activeTitle: '新对话',
  }),
  actions: {
    newChat() {
      this.messages = [{ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' }]
      this.activeTitle = '新对话'
    },
    async send(text: string, questionId?: number) {
      if (!this.messages.length) {
        this.messages.push({ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' })
      }
      this.messages.push({ role: 'user', text })
      this.activeTitle = text.slice(0, 12)
      this.typing = true
      try {
        const resp = await aiApi.chat({ message: text, question_id: questionId })
        this.messages.push({ role: 'ai', text: resp.reply })
      } catch (e) {
        this.messages.push({ role: 'ai', text: `出错了:${(e as Error).message}` })
      } finally {
        this.typing = false
      }
    },
  },
})
