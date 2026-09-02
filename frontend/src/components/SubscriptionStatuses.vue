<script setup lang="ts">
interface StatusItem {
  label: string
  count: number
  pct: number
  dotClass: string
}

const statuses: StatusItem[] = [
  { label: 'Активные', count: 150, pct: 83.3, dotClass: 'bg-emerald-400' },
  { label: 'В процессе автосписания', count: 12, pct: 6.7, dotClass: 'bg-yellow-400' },
  { label: 'Отменены', count: 18, pct: 12, dotClass: 'bg-red-400' }
]
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl">
    <h2 class="text-base font-semibold text-gray-200 mb-4">Статусы подписок</h2>
    <div class="space-y-3">
      <div
        v-for="status in statuses"
        :key="status.label"
        class="flex items-center justify-between text-sm"
      >
        <div class="flex items-center gap-2.5 text-gray-300">
          <span class="w-2 h-2 rounded-full inline-block" :class="status.dotClass"></span>
          <span>{{ status.label }}</span>
        </div>
        <div class="text-gray-400">
          <span class="text-white font-semibold">{{ status.count }}</span>
          ({{ status.pct }}%)
        </div>
      </div>
    </div>
  </div>
</template>
