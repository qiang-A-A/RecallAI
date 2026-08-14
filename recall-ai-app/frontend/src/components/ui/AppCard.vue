<script setup lang="ts">
/** 卡片组件:标准卡 / 交互卡(可点击)。 */
withDefaults(defineProps<{
  interactive?: boolean
  title?: string
}>(), { interactive: false, title: '' })

defineEmits<{ click: [event: MouseEvent] }>()
</script>

<template>
  <div
    class="bg-white border border-[#e5e3df] rounded-[14px] p-5 transition-all"
    :class="interactive ? 'cursor-pointer hover:shadow-md hover:-translate-y-[1px] hover:border-[#c8c4be]' : 'shadow-sm'"
    @click="interactive && $emit('click', $event)"
  >
    <h3 v-if="title" class="m-0 mb-1 text-[15px] font-semibold text-charcoal">{{ title }}</h3>
    <slot />
  </div>
</template>
