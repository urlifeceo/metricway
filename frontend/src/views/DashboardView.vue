<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { VueDatePicker } from "@vuepic/vue-datepicker"
import '@vuepic/vue-datepicker/dist/main.css'
import { useAnalyticsStore } from '@/stores/analytics'
import StatCard from '@/components/StatCard.vue'
import ActivityChart from '@/components/ActivityChart.vue'
import RetentionTable from '@/components/RetentionTable.vue'
import FunnelChart from '@/components/FunnelChart.vue'
import SubscriptionStatuses from '@/components/SubscriptionStatuses.vue'
import TrafficTable from '@/components/TrafficTable.vue'
import type { ActivityGranularity } from '@/types/analytics'

const store = useAnalyticsStore()
const projectToken = ref('')

function loadData() {
  if (!projectToken.value.trim()) return
  store.startPolling(projectToken.value, 10000)
}

function onGranularityChange(granularity: ActivityGranularity) {
  store.setGranularity(granularity)
  loadData()
}

function formatNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '—'
  return value.toLocaleString('ru-RU')
}

function formatRatio(value: number | undefined | null): string {
  if (value === undefined || value === null || value === 0) return '—'
  return `${value}:1`
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
          @change="loadData"
          type="text"
          placeholder="Project Token"
          class="bg-gray-900 border border-gray-800 focus:border-blue-500 text-sm rounded-full px-4 py-2 outline-none text-gray-200 placeholder-gray-500"
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
          @click="store.setPeriodPreset('this_month')"
          class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95"
        >
          Этот месяц
        </button>

        <button
          @click="store.setPeriodPreset('prev_month')"
          class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95"
        >
          Предыдущий месяц
        </button>

        <button
          @click="loadData"
          class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95 shadow-lg shadow-blue-500/20"
        >
          Обновить
        </button>
      </div>
    </header>

    <div v-if="store.loading && !store.financials" class="flex justify-center items-center py-32 text-gray-500">
      <span class="animate-pulse text-lg">Загрузка метрик...</span>
    </div>

    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4" v-if="store.financials">
        <StatCard title="Выручка" :value="formatNumber(store.financials.total_revenue)" />
        <StatCard title="MRR" :value="formatNumber(store.financials.mrr)" />
        <StatCard title="ARR" :value="formatNumber(store.financials.arr)" />
        <StatCard title="ARPPU" :value="formatNumber(store.financials.arppu)" />
        <StatCard title="Активные подписки" :value="store.financials.active_subscriptions" />
        <StatCard title="Прогнозный LTV" :value="formatNumber(store.financials.forecast_ltv)" />
        <StatCard title="Соотношение с CAC" :value="formatRatio(store.financials.ltv_cac_ratio)" accent="green" />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ActivityChart
          :data="store.activityData"
          :granularity="store.activityGranularity"
          @update:granularity="onGranularityChange"
        />

        <FunnelChart
          :data="store.funnelData"
          :project-token="projectToken"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" v-if="store.financials">
        <StatCard title="CR1 (Первый платеж)" :value="`${store.financials.cr_first}%`" />
        <StatCard title="CR2 (Повторный платеж)" :value="`${store.financials.cr_repeat}%`" />
        <StatCard title="Churn Rate, %" :value="`${store.financials.churn_rate}%`" />
        <div class="bg-gray-900 border border-gray-800 p-5 rounded-xl">
          <span class="text-xs font-medium text-gray-400 uppercase tracking-wider">Вид оттока</span>
          <select
            class="bg-gray-800 text-sm text-gray-200 rounded-lg px-3 py-2 mt-3 w-full border border-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option selected>по подписке</option>
            <option disabled>по активности</option>
            <option disabled>по платежам</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SubscriptionStatuses />
        <TrafficTable :data="store.trafficMetrics" :project-token="projectToken" />
      </div>

      <RetentionTable :data="store.retentionData" />
    </div>
  </div>
</template>
