<template>
  <div class="bg-gray-50 dark:bg-gray-800 p-5 rounded-xl border border-gray-200 dark:border-gray-700 overflow-x-auto">
    <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">Retention Cohorts</h3>
    <table class="w-full text-left text-sm text-gray-700 dark:text-gray-300">
      <thead class="bg-gray-100 dark:bg-gray-900 text-gray-500 dark:text-gray-400 uppercase text-xs">
        <tr>
          <th class="p-3">Когорта</th>
          <th class="p-3">Размер</th>
          <th class="p-3 text-center" v-for="m in 7" :key="m">
            M{{ m - 1 }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="cohort in data" :key="cohort.cohort_date" class="border-b border-gray-200 dark:border-gray-700">
          <td class="p-3 font-medium text-gray-900 dark:text-white">{{ cohort.cohort_date }}</td>
          <td class="p-3">{{ cohort.cohort_size }}</td>
          <td
            v-for="m in 7"
            :key="m"
            class="p-3 text-center font-semibold"
            :style="getHeatmapStyle(cohort.retention[m - 1])"
          >
            {{ cohort.retention[m - 1] !== undefined ? cohort.retention[m - 1] + '%' : '—' }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup lang="ts">
import type { CohortRetention } from '@/types/analytics'

defineProps<{
  data: CohortRetention[]
}>()

const getHeatmapStyle = (val: number | undefined) => {
  if (val === undefined) return {}
  const opacity = Math.min(val / 100, 1)
  return {
    backgroundColor: `rgba(59, 130, 246, ${opacity * 0.6})`,
    color: opacity > 0.4 ? '#ffffff' : undefined
  }
}
</script>
