<script setup lang="ts">
import { ref, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import type { TrafficMetric } from '@/types/analytics'

const props = defineProps<{
  data: TrafficMetric[]
  projectToken: string
}>()

const store = useAnalyticsStore()

const spendInputs = ref<Record<string, string>>({})
const timers: Record<string, ReturnType<typeof setTimeout>> = {}

watch(
  () => props.data,
  (newData) => {
    const next: Record<string, string> = {}
    for (const row of newData) {
      next[row.source] = spendInputs.value[row.source] ?? String(row.spend || '')
    }
    spendInputs.value = next
  },
  { immediate: true }
)

function onSpendInput(source: string) {
  if (timers[source]) {
    clearTimeout(timers[source])
  }
  timers[source] = setTimeout(() => {
    const raw = spendInputs.value[source]
    if (raw === undefined || raw === '') return
    const spend = parseFloat(raw.replace(',', '.'))
    if (Number.isNaN(spend) || spend < 0) return
    if (props.projectToken) {
      store.saveTrafficSpend(props.projectToken, source, spend)
    }
  }, 500)
}
</script>

<template>
  <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
    <div class="p-6 border-b border-gray-800">
      <h2 class="text-base font-semibold text-gray-200">Трафик</h2>
    </div>
    <div class="overflow-x-auto">
      <table class="w-full text-left text-sm text-gray-300">
        <thead class="bg-gray-900/50 text-gray-400 border-b border-gray-800 text-xs uppercase tracking-wider">
          <tr>
            <th class="py-3 px-6">Источник</th>
            <th class="py-3 px-6">Количество</th>
            <th class="py-3 px-6">Купили</th>
            <th class="py-3 px-6">Конверсия</th>
            <th class="py-3 px-6">Расход</th>
            <th class="py-3 px-6">CAC</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-800/60">
          <tr v-for="row in data" :key="row.source" class="hover:bg-gray-800/40 transition">
            <td class="py-4 px-6 font-medium text-white">{{ row.source || '—' }}</td>
            <td class="py-4 px-6">{{ row.acquisitions }}</td>
            <td class="py-4 px-6">{{ row.buyers }}</td>
            <td class="py-4 px-6">{{ row.conversion_rate }}%</td>
            <td class="py-4 px-6">
              <input
                v-model="spendInputs[row.source]"
                @input="onSpendInput(row.source)"
                type="text"
                placeholder="Введите сумму"
                class="bg-gray-800 border border-gray-700 focus:border-blue-500 text-sm rounded-lg px-3 py-1.5 outline-none text-gray-200 w-32"
              />
            </td>
            <td class="py-4 px-6">{{ row.cac }}</td>
          </tr>
          <tr v-if="!data?.length">
            <td colspan="6" class="py-8 text-center text-gray-500">Нет данных</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>
