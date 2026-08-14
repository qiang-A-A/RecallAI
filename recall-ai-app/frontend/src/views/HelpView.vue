<script setup lang="ts">
/** 帮助页:FAQ 手风琴。 */
const faqs = [
  { q: '如何录入一道错题?', a: '点击错题集页面的「录入错题」按钮,支持拍照、截图、文本三种方式。拍照后 AI 自动识别并诊断知识点。' },
  { q: '3 级提示是什么?', a: '复习时依次展示考点 → 思路 → 完整解析,尽量先自己思考再逐步解锁,学习效果更好。' },
  { q: '如何更换 AI 模型?', a: '前往「设置与帮助 → AI 模型设置」,选择供应商并配置 API Key 即可。' },
  { q: '数据会丢失吗?', a: '数据实时云端同步并自动备份,更换设备登录同一账号即可恢复。' },
  { q: '如何导出错题报告?', a: '在错题集页点击「导出」,支持 PDF / Markdown 两种格式。' },
]
</script>

<template>
  <div class="max-w-[700px] mx-auto bg-white border border-[#e5e3df] rounded-[16px] p-5 shadow-xs">
    <div class="flex items-center justify-between mb-3.5">
      <h3 class="m-0 text-[16px] font-semibold text-charcoal">帮助中心</h3>
      <span class="text-[11px] font-semibold text-primary-deep bg-tint-lavender rounded-full px-2.5 py-0.5">常见问题</span>
    </div>
    <div>
      <details v-for="f in faqs" :key="f.q"
               class="py-3 border-b border-[#f3f1ea] last:border-b-0">
        <summary class="cursor-pointer text-sm font-semibold text-charcoal list-none
                        flex justify-between items-center">
          {{ f.q }}
          <svg viewBox="0 0 24 24" class="w-4 h-4 text-stone" fill="none"
               stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
            <path d="M6 9l6 6 6-6" />
          </svg>
        </summary>
        <p class="text-[13px] text-slate mt-2 m-0">{{ f.a }}</p>
      </details>
    </div>
    <button class="mt-4 text-xs font-semibold text-charcoal bg-white border border-[#c8c4be]
                   rounded-lg px-3.5 py-2 hover:border-primary hover:text-primary">
      意见反馈
    </button>
  </div>
</template>
