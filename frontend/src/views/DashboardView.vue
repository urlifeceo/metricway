<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { VueDatePicker } from "@vuepic/vue-datepicker"
import '@vuepic/vue-datepicker/dist/main.css'
import { useAnalyticsStore } from '@/stores/analytics'
import DauChart from '@/components/DauChart.vue'
import RetentionTable from '@/components/RetentionTable.vue'
import FunnelChart from '@/components/FunnelChart.vue'

const store = useAnalyticsStore()
const projectToken = ref('secretit')

function loadData() {
  store.startPolling(projectToken.value, 10000)
}

function exportUtmCsv() {
  // const [fromDate, toDate] = store.dateRange
  // const params = new URLSearchParams({
  //   project_token: projectToken.value,
  //   from_date: fromDate.toISOString(),
  //   to_date: toDate.toISOString()
  // })
  // window.open(`/api/v1/analytics/export/utm?${params.toString()}`, '_blank')
}

watch(() => store.dateRange, () => {
  loadData()
})

onMounted(() => {
  loadData()
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<template>
  <div class="min-h-screen bg-gray-950 text-gray-100 p-6 md:p-10 font-sans">
    <header class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-8 border-b border-gray-800 pb-6">
      <div>
        <h1 class="text-3xl font-bold text-blue-500 tracking-tight">TgMetrics</h1>
        <p class="text-xs text-gray-400 mt-1">Панель управления аналитикой</p>
      </div>

      <div class="flex flex-wrap items-center gap-3 w-full lg:w-auto">
        <input
          v-model="projectToken"
          type="text"
          placeholder="Project Token"
          class="bg-gray-900 border border-gray-800 focus:border-blue-500 text-sm rounded-lg px-3 py-2 outline-none text-gray-200"
        />
        
        <div class="w-64">
          <VueDatePicker
            v-model="store.dateRange"
            range
            dark
            :enable-time-picker="false"
            auto-apply
            placeholder="Выберите период"
          />
        </div>

        <button
          @click="loadData"
          class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2.5 rounded-lg transition active:scale-95 shadow-lg shadow-blue-500/20"
        >
          Обновить
        </button>
      </div>
    </header>

    <div v-if="store.loading && !store.financials" class="flex justify-center items-center py-32 text-gray-500">
      <span class="animate-pulse text-lg">Загрузка метрик...</span>
    </div>

    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" v-if="store.financials">
        <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">Выручка</span>
          <div class="text-2xl font-bold text-white mt-2">{{ store.financials.total_revenue.toLocaleString() }}</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">Конверсия (CR)</span>
          <div class="text-2xl font-bold text-emerald-400 mt-2">{{ store.financials.conversion_rate }}%</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">ARPU</span>
          <div class="text-2xl font-bold text-white mt-2">{{ store.financials.arpu }}</div>
        </div>
        <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">ARPPU</span>
          <div class="text-2xl font-bold text-white mt-2">{{ store.financials.arppu }}</div>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div class="bg-gray-900 border border-gray-800 p-6 rounded-xl">
          <h2 class="text-base font-semibold text-gray-200 mb-4">Динамика DAU</h2>
          <div class="h-72">
            <DauChart :data="store.dauData" />
          </div>
        </div>

        <FunnelChart 
          :data="store.funnelData" 
          :project-token="projectToken" 
        />
      </div>

      <RetentionTable :data="store.retentionData" />

      <div class="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <div class="p-6 border-b border-gray-800 flex justify-between items-center">
          <h2 class="text-base font-semibold text-gray-200">Источники трафика</h2>
          <button
            @click="exportUtmCsv"
            class="bg-gray-800 hover:bg-gray-700 text-gray-200 text-xs font-medium px-3 py-1.5 rounded border border-gray-700 transition"
          >
            Скачать CSV
          </button>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm text-gray-300">
            <thead class="bg-gray-900/50 text-gray-400 border-b border-gray-800 text-xs uppercase tracking-wider">
              <tr>
                <th class="py-3 px-6">Source</th>
                <th class="py-3 px-6">Campaign</th>
                <th class="py-3 px-6">Переходы</th>
                <th class="py-3 px-6">Покупатели</th>
                <th class="py-3 px-6">Выручка</th>
                <th class="py-3 px-6">CR</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-800/60">
              <tr v-for="(row, idx) in store.utmMetrics" :key="idx" class="hover:bg-gray-800/40 transition">
                <td class="py-4 px-6 font-medium text-white">{{ row.source || '—' }}</td>
                <td class="py-4 px-6 text-gray-400">{{ row.campaign || '—' }}</td>
                <td class="py-4 px-6">{{ row.acquisitions }}</td>
                <td class="py-4 px-6">{{ row.buyers }}</td>
                <td class="py-4 px-6 text-emerald-400 font-medium">${{ row.revenue }}</td>
                <td class="py-4 px-6">{{ row.conversion_rate }}%</td>
              </tr>
              <tr v-if="!store.utmMetrics?.length">
                <td colspan="6" class="py-8 text-center text-gray-500">Нет данных по кампаниям</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>