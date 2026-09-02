<script setup lang="ts">
defineProps<{
  title: string
  value: string | number
  accent?: 'default' | 'green'
}>()
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
    <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">{{ title }}</span>
    <div
      class="text-2xl font-bold mt-2"
      :class="accent === 'green' ? 'text-emerald-400' : 'text-white'"
    >
      {{ value }}
    </div>
  </div>
</template>
