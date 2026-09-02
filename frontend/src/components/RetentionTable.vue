<template>
  <div class="bg-gray-800 p-5 rounded-xl border border-gray-700 overflow-x-auto">
    <h3 class="text-lg font-semibold text-white mb-4">Retention Cohorts</h3>
    <table class="w-full text-left text-sm text-gray-300">
      <thead class="bg-gray-900 text-gray-400 uppercase text-xs">
        <tr>
          <th class="p-3">Когорта</th>
          <th class="p-3">Размер</th>
          <th class="p-3 text-center" v-for="day in [0, 1, 3, 7, 14, 30]" :key="day">
            Day {{ day }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="cohort in data" :key="cohort.cohort_date" class="border-b border-gray-700">
          <td class="p-3 font-medium text-white">{{ cohort.cohort_date }}</td>
          <td class="p-3">{{ cohort.cohort_size }}</td>
          <td
            v-for="day in [0, 1, 3, 7, 14, 30]"
            :key="day"
            class="p-3 text-center font-semibold"
            :style="getHeatmapStyle(cohort.retention[day])"
          >
            {{ cohort.retention[day] !== undefined ? cohort.retention[day] + '%' : '-' }}
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
defineProps({
  data: Array
})

const getHeatmapStyle = (val) => {
  if (val === undefined) return {}
  const opacity = Math.min(val / 100, 1)
  return {
    backgroundColor: `rgba(59, 130, 246, ${opacity * 0.6})`,
    color: opacity > 0.4 ? '#ffffff' : '#9ca3af'
  }
}
</script>