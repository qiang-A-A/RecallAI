/** AI 回复渲染:Markdown + LaTeX(KaTeX)。
 *
 * 关键顺序(避免 markdown-it 把公式符号当作普通字符):
 *  1) 占位符保护所有公式区段
 *  2) markdown-it 处理剩余文本
 *  3) 占位符替换回 KaTeX 渲染后的 HTML
 */
import MarkdownIt from 'markdown-it'
import katex from 'katex'

const md = new MarkdownIt({
  html: false,           // 不解析原始 HTML(防 XSS)
  linkify: true,         // 自动识别 URL
  breaks: true,         // 单换行转 <br>(AI 回复常用单换行分段)
  typographer: false,
})

/** 把 AI 回复文本渲染成安全的 HTML(支持 Markdown + LaTeX) */
export function renderAiReply(text: string): string {
  if (!text) return ''
  // 1) 占位符保护公式块:$$...$$ / \[...\] → BLOCK_N;$...$/ \(...\) → INLINE_N
  const mathBlocks: string[] = []
  const mathInlines: string[] = []
  // 占位符:用普通 ASCII(§/§),避免 NUL/不可见字符被 markdown-it 过滤
  const placeholder = (i: number, type: 'B' | 'I') => `§§MATH_${type}_${i}§§`
  let protected_ = text
  // $$...$$ 块级
  protected_ = protected_.replace(/\$\$([\s\S]+?)\$\$/g, (_, m) => {
    const i = mathBlocks.length
    mathBlocks.push(m)
    return placeholder(i, 'B')
  })
  // \[...\] 块级
  protected_ = protected_.replace(/\\\[([\s\S]+?)\\\]/g, (_, m) => {
    const i = mathBlocks.length
    mathBlocks.push(m)
    return placeholder(i, 'B')
  })
  // \(...\) 行内
  protected_ = protected_.replace(/\\\(([\s\S]+?)\\\)/g, (_, m) => {
    const i = mathInlines.length
    mathInlines.push(m)
    return placeholder(i, 'I')
  })
  // $...$ 行内(单行)
  protected_ = protected_.replace(/\$([^$\n]+?)\$/g, (_, m) => {
    const i = mathInlines.length
    mathInlines.push(m)
    return placeholder(i, 'I')
  })
  // 2) markdown 处理
  let html = md.render(protected_)
  // 3) 回填公式:块级
  html = html.replace(/§§MATH_B_(\d+)§§/g, (_, i) => {
    try {
      return katex.renderToString(mathBlocks[Number(i)].trim(), { displayMode: true, throwOnError: false })
    } catch { return `<code class="math-error">${mathBlocks[Number(i)]}</code>` }
  })
  // 行内
  html = html.replace(/§§MATH_I_(\d+)§§/g, (_, i) => {
    try {
      return katex.renderToString(mathInlines[Number(i)].trim(), { displayMode: false, throwOnError: false })
    } catch { return `<code class="math-error">${mathInlines[Number(i)]}</code>` }
  })
  return html
}