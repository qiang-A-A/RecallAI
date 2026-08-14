<script setup lang="ts">
/** Toast 提示:全局单例,通过 composable 触发。 */
defineProps<{ message: string; show: boolean }>()
</script>

<template>
  <Transition
    enter-active-class="transition-all duration-300 ease-[cubic-bezier(.16,1,.3,1)]"
    enter-from-class="opacity-0 translate-y-5"
    leave-active-class="transition-all duration-300"
    leave-to-class="opacity-0 translate-y-5"
  >
    <div
      v-if="show"
      class="fixed bottom-6 left-1/2 -translate-x-1/2 z-[400] bg-charcoal text-white
             px-5 py-2.5 rounded-[10px] text-sm shadow-lg"
      role="status"
      aria-live="polite"
    >
      {{ message }}
    </div>
  </Transition>
</template>
