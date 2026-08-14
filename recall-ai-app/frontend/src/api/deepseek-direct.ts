/** DeepSeek 浏览器直连模块(单文件静态版使用)。
 *
 * 静态版无法依赖后端代理,因此:
 * - API Key 存储在 localStorage(用户本地,不落服务器)
 * - 直接 fetch DeepSeek Chat Completions(官方支持 CORS,含 file:// 的 Origin:null)
 * - 封装 chat / analyze(学科·知识点·错因归档)/ ping(测试连接)三类能力
 */

const BASE_URL = 'https://api.deepseek.com/chat/completions'
const MODEL = 'deepseek-chat'
const KEY_STORAGE = 'recall_deepseek_key'

export function getApiKey(): string {
  try { return localStorage.getItem(KEY_STORAGE) || '' } catch { return '' }
}
export function setApiKey(key: string): void {
  try { localStorage.setItem(KEY_STORAGE, key.trim()) } catch { /* ignore */ }
}
export function clearApiKey(): void {
  try { localStorage.removeItem(KEY_STORAGE) } catch { /* ignore */ }
}

interface DSChoice { message?: { content?: string } }
interface DSResp { choices?: DSChoice[] }

/** 通用调用:发消息到 DeepSeek,返回文本 */
async function call(messages: { role: string; content: string }[], opts: { temperature?: number; max_tokens?: number; json?: boolean } = {}): Promise<string> {
  const key = getApiKey()
  if (!key) throw new Error('请先在「设置」页配置 DeepSeek API Key')
  const resp = await fetch(BASE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${key}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature: opts.temperature ?? 0.3,
      max_tokens: opts.max_tokens ?? 2048,
      ...(opts.json ? { response_format: { type: 'json_object' } } : {}),
    }),
  }).catch((e) => {
    // 浏览器原生 fetch 错误是 "Failed to fetch" / "NetworkError when attempting to fetch"
    // 多数情况是浏览器直连 DeepSeek 受限(file:// + 自定义 Authorization 头 / 网络拦截 / 浏览器策略)
    // 给出明确诊断而不是模糊错误
    const msg = String((e as Error).message || e)
    if (/Failed to fetch|NetworkError|fetch failed/i.test(msg)) {
      throw new Error('无法连接到 DeepSeek(网络层失败)。可能原因:① 网络无法访问 api.deepseek.com(防火墙/代理);② 浏览器禁止 file:// 协议的跨域 fetch。解决:启动本地 FastAPI 后端运行版(localhost:5173),由后端代理 DeepSeek。')
    }
    throw new Error(`网络错误:${msg}`)
  })
  if (resp.status === 401) throw new Error('API Key 无效(401),请在设置页检查后重新配置')
  if (resp.status === 402) throw new Error('API 余额不足(402)')
  if (resp.status === 429) throw new Error('请求过于频繁(429),请稍后重试')
  if (!resp.ok) {
    const body = await resp.text().catch(() => '')
    throw new Error(`DeepSeek 请求失败(${resp.status})${body ? ': ' + body.slice(0, 120) : ''}`)
  }
  const data = (await resp.json()) as DSResp
  const content = data.choices?.[0]?.message?.content
  if (!content) throw new Error('DeepSeek 返回为空')
  return content
}

/** AI 对话(答疑) */
export async function chatDirect(message: string, questionContext = ''): Promise<string> {
  const user = questionContext ? `题目上下文:${questionContext}\n\n学生提问:${message}` : message
  return call([
    { role: 'system', content: '你是 Recall AI 学习助手,面向高中/大学/考研学生。回答要分步、可理解,先引导思考再给结论,避免直接贴答案。' },
    { role: 'user', content: user },
  ], { temperature: 0.6 })
}

/** AI 自动归档:学科 / 知识点 / 错因 / 答案 / 题型 / 难度 */
export async function analyzeDirect(text: string, sourceType: string): Promise<{
  ok: boolean; subject?: string; q_type?: string; difficulty?: string; kp_name?: string;
  answer?: string; wrong_reason?: string; reason?: string; detail?: string
}> {
  try {
    const raw = await call([
      {
        role: 'system',
        content: '你是 Recall AI 的智能归档引擎。根据学生提供的题目内容,自动完成结构化识别。输出严格 JSON,不要其他文字:{"subject":"数学|物理|化学|生物|英语|语文|其他","q_type":"choice|solve|proof|calc|other","difficulty":"easy|mid|hard","kp_name":"核心知识点名称","answer":"参考答案","wrong_reason":"概念混淆|计算失误|审题偏差|方法不熟|其他","reason":"一句话说明为什么这样归类"}',
      },
      { role: 'user', content: `来源方式: ${sourceType}\n题目内容:\n${text}` },
    ], { temperature: 0.2, max_tokens: 1024, json: true })
    const d = JSON.parse(raw)
    return {
      ok: true,
      subject: String(d.subject || '数学'),
      q_type: String(d.q_type || 'solve'),
      difficulty: String(d.difficulty || 'mid'),
      kp_name: String(d.kp_name || '待确认'),
      answer: String(d.answer || ''),
      wrong_reason: String(d.wrong_reason || '其他'),
      reason: String(d.reason || ''),
    }
  } catch (e) {
    // 网络/Key 失败 → 本地启发式兜底,保持"AI 识别"体感
    return localAnalyze(text, sourceType, (e as Error).message)
  }
}

/** 本地启发式识别:无 Key 或网络失败时兜底(关键词 + 启发规则,非真 AI) */
export function localAnalyze(text: string, sourceType: string, upstreamErr?: string): {
  ok: boolean; subject: string; q_type: string; difficulty: string; kp_name: string;
  answer: string; wrong_reason: string; reason: string; detail?: string
} {
  const t = (text || '').trim()
  const lower = t.toLowerCase()
  // 学科启发
  let subject = '数学', kp = '待用户标注'
  // 含数学符号/数字特征则偏数学(更宽容,避免空文本被误判)
  if (/[0-9²³√π∑∫]/.test(t)) subject = '数学'
  const KW = [
    [/导数|单调|极值|积分|极限|矩阵|椭圆|抛物线|双曲线|圆锥曲线|圆周率|等差数列|等比数列|对数|指数|三角函数/, '数学', '高考数学'],
    [/自由落体|重力|加速度|匀速|受力|摩擦力|动量|电场|磁场|电路|欧姆|焦耳|牛顿/, '物理', '物理力学/电磁'],
    [/化学式|氧化|还原|反应|摩尔|电解质|催化剂|有机|无机|元素|化合价|沉淀/, '化学', '化学反应'],
    [/翻译|语法|时态|语态|单词|词组|完形填空|阅读理解|作文|英语/, '英语', '英语语言'],
    [/DNA|RNA|基因|细胞|蛋白质|生物|生态系统|遗传|酶/, '生物', '生物学'],
    [/古诗|文言|字词|成语|句子|阅读|作文|段落/, '语文', '语文语言'],
  ] as const
  for (const [re, subj, kpName] of KW) {
    if (re.test(t)) { subject = subj; kp = kpName; break }
  }
  // 题型启发
  let qType: 'choice' | 'solve' | 'proof' | 'calc' | 'other' = 'solve'
  if (/(请选择|下列说法正确的是|哪个是|的是)/.test(t)) qType = 'choice'
  else if (/(证明|求证)/.test(t)) qType = 'proof'
  else if (/(求|计算|等于|求值)/.test(t)) qType = 'calc'
  else if (!/[\?\uff1f]/.test(t) && t.length < 20) qType = 'other'
  // 难度启发
  let difficulty: 'easy' | 'mid' | 'hard' = 'mid'
  if (t.length < 30) difficulty = 'easy'
  else if (t.length > 120 || /二阶|积分|复合|联立|圆锥/.test(t)) difficulty = 'hard'
  // 错因启发(从文本里找常见错误关键词)
  let wrongReason = '待用户标注'
  if (/符号|概念|定义|混淆|记错/.test(t)) wrongReason = '概念混淆'
  else if (/计算|得数|答案|等于|算错/.test(t)) wrongReason = '计算失误'
  else if (/审题|题意|题目要求|忽略/.test(t)) wrongReason = '审题偏差'
  else if (/公式|方法|解法|步骤|不会/.test(t)) wrongReason = '方法不熟'
  const detail = upstreamErr
    ? `本地启发识别(DeepSeek 不可用: ${upstreamErr.slice(0, 50)}${upstreamErr.length > 50 ? '...' : ''})`
    : '本地启发识别'
  return {
    ok: true, subject, q_type: qType, difficulty, kp_name: kp,
    answer: '', wrong_reason: wrongReason,
    reason: detail, detail,
  }
}

/** 3 级提示梯度(考点→思路→解析) */
export async function hintsDirect(questionText: string, answer: string): Promise<string[]> {
  const raw = await call([
    { role: 'system', content: '你是耐心的高中/大学教师。为学生生成 3 级提示:①核心考点 ②思路引导 ③完整解析。仅输出 JSON:{"hints":["考点","思路","解析"]}' },
    { role: 'user', content: `题目:${questionText}\n参考答案:${answer}` },
  ], { temperature: 0.4, json: true })
  try {
    const d = JSON.parse(raw)
    const h = (d.hints as string[]) || []
    return (h.length >= 3 ? h : [...h, '思路:结合考点逐步推导', '解析:由 AI 讲解']).slice(0, 3)
  } catch {
    return ['考点:' + questionText.slice(0, 30), '思路:结合考点逐步推导', '解析:由 AI 讲解']
  }
}

/** 测试连接:发一条极短消息验证 Key 有效性 */
export async function pingDirect(): Promise<{ ok: boolean; message: string }> {
  try {
    const key = getApiKey()
    if (!key) return { ok: false, message: 'API Key 未配置,请先在设置中保存 Key' }
    const resp = await fetch(BASE_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${key}` },
      body: JSON.stringify({
        model: MODEL,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 4,
      }),
    }).catch((e) => {
      const msg = String((e as Error).message || e)
      return { __networkError: msg } as unknown as Response
    })
    if (resp.status === 401) return { ok: false, message: 'Key 无效(401 Unauthorized),请检查是否正确' }
    if (resp.ok) return { ok: true, message: '连接成功,API Key 有效 ✓' }
    // 网络层失败
    if ((resp as unknown as { __networkError?: string }).__networkError) {
      return { ok: false, message: '无法连接 DeepSeek(网络层失败)。可能浏览器/网络不允许直连 DeepSeek,请改用运行版(localhost:5173)由后端代理。' }
    }
    return { ok: false, message: `连接失败(${resp.status})` }
  } catch (e) {
    return { ok: false, message: `网络错误:${(e as Error).message}` }
  }
}
