<script setup lang="ts">
/** 按钮组件:Primary / Secondary / Ghost / Danger / Glass 五变体。 */
withDefaults(defineProps<{
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'glass'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
}>(), { variant: 'primary', size: 'md', disabled: false })

defineEmits<{ click: [event: MouseEvent] }>()
</script>

<template>
  <button
    class="inline-flex items-center justify-center gap-2 rounded-lg font-semibold transition-all
           active:scale-[0.97] disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
    :class="[
      variant === 'primary' && 'bg-primary text-white shadow-sm hover:bg-primary-pressed',
      variant === 'secondary' && 'bg-white text-charcoal border border-[#c8c4be] hover:border-primary hover:text-primary',
      variant === 'ghost' && 'text-slate hover:bg-[#f6f5f4] hover:text-charcoal',
      variant === 'danger' && 'bg-error text-white hover:bg-[#b3272b]',
      variant === 'glass' && 'backdrop-blur-md bg-white/60 border border-white/60 text-primary-deep shadow-[inset_0_1px_0_rgba(255,255,255,.7)]',
      size === 'sm' && 'px-3 py-1.5 text-xs',
      size === 'md' && 'px-4 py-2.5 text-sm',
      size === 'lg' && 'px-6 py-3 text-[15px]',
    ]"
    :disabled="disabled"
    @click="$emit('click', $event)"
  >
    <slot />
  </button>
</template>
