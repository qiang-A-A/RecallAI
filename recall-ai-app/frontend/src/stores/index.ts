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
    /** 编辑错题:调 API + 更新本地 store */
    async update(id: number, payload: Parameters<typeof questionApi.update>[1]) {
      const updated = await questionApi.update(id, payload)
      const idx = this.items.findIndex((q) => q.id === id)
      if (idx >= 0) this.items[idx] = updated
      this.refreshTick++
      return updated
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
    /** 复习自评后:按 SM-2 语义更新 mastery(与后端 compute_mastery 一致) */
    applyReview(id: number, status: 'mastered' | 'fuzzy' | 'failed') {
      const item = this.items.find((q) => q.id === id)
      if (item) {
        // 与后端 compute_mastery 对齐: mastered→0.7+reps加成, fuzzy→0.5, failed→0.3
        const base = { mastered: 0.72, fuzzy: 0.5, failed: 0.3 }[status]
        item.mastery = base
        item.review_count = (item.review_count ?? 0) + 1
      }
      this.refreshTick++
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
    activeConvId: '' as string,
    /** 对话历史:[{ id, title, messages, created_at }],localStorage 持久化 */
    conversations: [] as { id: string; title: string; messages: ChatMessage[]; created_at: string }[],
  }),
  actions: {
    /** 从 localStorage 恢复历史会话 */
    loadConversations() {
      try {
        const raw = localStorage.getItem('recall_conversations')
        if (raw) {
          this.conversations = JSON.parse(raw)
          // 恢复上次会话
          const last = this.conversations[0]
          if (last) {
            this.activeConvId = last.id
            this.messages = [...last.messages]
            this.activeTitle = last.title
          }
        }
      } catch { /* ignore */ }
    },
    _persist() {
      try { localStorage.setItem('recall_conversations', JSON.stringify(this.conversations)) } catch { /* ignore */ }
    },
    /** 新建对话:保存当前会话(若有内容)并创建空白会话 */
    newChat() {
      // 保存当前会话到历史(若已有用户消息)
      if (this.activeConvId && this.messages.some((m) => m.role === 'user')) {
        const conv = this.conversations.find((c) => c.id === this.activeConvId)
        if (conv) {
          conv.messages = [...this.messages]
          conv.title = this.activeTitle
        }
        this._persist()
      }
      // 创建新会话
      this.activeConvId = `conv-${Date.now()}`
      this.messages = [{ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' }]
      this.activeTitle = '新对话'
      // 新会话也加入历史(标题为"新对话",可在提问后更新)
      this.conversations.unshift({ id: this.activeConvId, title: '新对话', messages: [...this.messages], created_at: new Date().toISOString() })
      this._persist()
    },
    /** 打开历史会话 */
    openConversation(id: string) {
      const conv = this.conversations.find((c) => c.id === id)
      if (!conv) return
      this.activeConvId = id
      this.messages = [...conv.messages]
      this.activeTitle = conv.title
    },
    /** 删除历史会话 */
    deleteConversation(id: string) {
      this.conversations = this.conversations.filter((c) => c.id !== id)
      this._persist()
      // 若删除的是当前会话,回到新对话
      if (this.activeConvId === id) {
        this.activeConvId = ''
        this.messages = [{ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' }]
        this.activeTitle = '新对话'
      }
    },
    async send(text: string, questionId?: number) {
      if (!this.messages.length) {
        this.messages.push({ role: 'ai', text: '你好,我是 Recall AI 学习助手。把不会的题拍给我,或直接提问 —— 我可以帮你诊断知识点、分步讲解、生成变式题。' })
      }
      this.messages.push({ role: 'user', text })
      this.activeTitle = text.slice(0, 12)
      // 新建会话的首条提问:创建会话记录
      if (!this.activeConvId) {
        this.activeConvId = `conv-${Date.now()}`
        this.conversations.unshift({ id: this.activeConvId, title: this.activeTitle, messages: [...this.messages], created_at: new Date().toISOString() })
      } else {
        // 更新历史中该会话的标题/消息
        const conv = this.conversations.find((c) => c.id === this.activeConvId)
        if (conv) {
          conv.title = this.activeTitle
          conv.messages = [...this.messages]
        }
      }
      this._persist()
      this.typing = true
      try {
        const resp = await aiApi.chat({ message: text, question_id: questionId })
        this.messages.push({ role: 'ai', text: resp.reply })
        // 更新历史中的 AI 回复
        const conv = this.conversations.find((c) => c.id === this.activeConvId)
        if (conv) conv.messages = [...this.messages]
        this._persist()
      } catch (e) {
        this.messages.push({ role: 'ai', text: `出错了:${(e as Error).message}` })
      } finally {
        this.typing = false
      }
    },
  },
})
