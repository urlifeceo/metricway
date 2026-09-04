<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    title: string
    value: string | number
    accent?: 'default' | 'green'
    delta?: number | null
    invertDelta?: boolean
  }>(),
  {
    accent: 'default',
    delta: null,
    invertDelta: false
  }
)

const deltaInfo = computed(() => {
  if (props.delta === null || props.delta === undefined || !Number.isFinite(props.delta)) {
    return null
  }
  const up = props.delta >= 0
  const good = props.invertDelta ? !up : up
  return {
    text: `${up ? '▲' : '▼'} ${up ? '+' : '−'}${Math.abs(props.delta).toFixed(1)}%`,
    colorClass: good ? 'text-emerald-400' : 'text-red-400'
  }
})
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl h-full flex flex-col min-h-[104px]">
    <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">{{ title }}</span>
    <div
      class="font-bold mt-2 text-xl xl:text-2xl tabular-nums whitespace-nowrap overflow-hidden text-ellipsis"
      :class="accent === 'green' ? 'text-emerald-400' : 'text-white'"
    >
      {{ value }}
    </div>
    <div class="text-xs mt-auto pt-1.5 h-4 flex items-center" :class="deltaInfo ? deltaInfo.colorClass : 'text-transparent'">
      {{ deltaInfo ? deltaInfo.text : '·' }}
    </div>
  </div>
</template>
