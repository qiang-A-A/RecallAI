<script setup lang="ts">
/** 徽章组件:AI / 用户 / 系统 / 警告 / 完成 / 错误 / 灰。 */
withDefaults(defineProps<{
  variant?: 'ai' | 'user' | 'sys' | 'warn' | 'done' | 'error' | 'gray'
}>(), { variant: 'ai' })
</script>

<template>
  <span
    class="inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold whitespace-nowrap"
    :class="{
      ai: 'bg-tint-lavender text-primary-deep',
      user: 'bg-tint-sky text-[#005bab]',
      sys: 'bg-tint-mint text-[#0a7a23]',
      warn: 'bg-tint-peach text-[#9c3f00]',
      done: 'bg-tint-mint text-[#0a6b1f]',
      error: 'bg-[#fde0ec] text-[#a0233c]',
      gray: 'bg-[#f6f5f4] text-steel border border-[#e5e3df]',
    }[variant]"
  >
    <slot />
  </span>
</template>
