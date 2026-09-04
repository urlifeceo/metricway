<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { VueDatePicker } from "@vuepic/vue-datepicker"
import '@vuepic/vue-datepicker/dist/main.css'
import { useAnalyticsStore } from '@/stores/analytics'
import { useProjectsStore } from '@/stores/projects'
import { useThemeStore } from '@/stores/theme'
import StatCard from '@/components/StatCard.vue'
import ActivityChart from '@/components/ActivityChart.vue'
import RetentionTable from '@/components/RetentionTable.vue'
import FunnelChart from '@/components/FunnelChart.vue'
import SubscriptionStatuses from '@/components/SubscriptionStatuses.vue'
import TrafficTable from '@/components/TrafficTable.vue'
import ProductMappings from '@/components/ProductMappings.vue'
import { formatNumber, formatRatio, calcDelta } from '@/utils/format'
import type { ActivityGranularity, PeriodPreset, FinancialMetrics } from '@/types/analytics'

const store = useAnalyticsStore()
const projectsStore = useProjectsStore()
const themeStore = useThemeStore()

const showDatePicker = ref(false)
const newProjectName = ref('')
const showCreateModal = computed(() => projectsStore.showCreateModal)

const periodPresets: Array<{ id: PeriodPreset; label: string }> = [
  { id: 'this_month', label: 'Текущий месяц' },
  { id: 'last_3_months', label: '3 месяца' },
  { id: 'this_year', label: 'Этот год' }
]

const themeIcon = computed(() => {
  if (themeStore.mode === 'system') return ''
  return themeStore.mode === 'dark' ? '🌙' : '☀️'
})

function loadData() {
  if (!projectsStore.currentToken) return
  store.startPolling(projectsStore.currentToken, 10000)
}

function onProjectChange() {
  const token = projectsStore.currentToken
  store.stopPolling()
  if (!token) return
  store.fetchFunnelConfig(token).then(() => {
    store.fetchAvailableEvents(token)
    loadData()
  })
}

function onGranularityChange(granularity: ActivityGranularity) {
  store.setGranularity(granularity)
  loadData()
}

function onPreset(preset: PeriodPreset) {
  store.setPeriodPreset(preset)
  showDatePicker.value = false
}

function onCustomToggle() {
  showDatePicker.value = !showDatePicker.value
}

function onCustomDateChange() {
  store.periodPreset = null
  if (store.dateRange?.[0] && store.dateRange?.[1]) {
    store.setDateRange(store.dateRange)
  }
}

function onManualDateChange() {
  store.periodPreset = null
}

function d(field: keyof FinancialMetrics): number | null {
  if (!store.financials || !store.financialsPrev) return null
  return calcDelta(
    store.financials[field] as number,
    store.financialsPrev[field] as number
  )
}

function openCreateModal() {
  newProjectName.value = ''
  projectsStore.createdProject = null
  projectsStore.error = null
  projectsStore.showCreateModal = true
}

async function createProject() {
  const name = newProjectName.value.trim()
  if (!name) return
  await projectsStore.createProject(name)
}

function closeCreateModal() {
  projectsStore.showCreateModal = false
  projectsStore.createdProject = null
  projectsStore.error = null
}

async function copyToken() {
  if (!projectsStore.createdProject) return
  try {
    await navigator.clipboard.writeText(projectsStore.createdProject.project_token)
  } catch {
    // clipboard недоступен — токен виден в модалке вручную
  }
}

watch(() => store.dateRange, () => {
  loadData()
})

onMounted(() => {
  projectsStore.fetchProjects().then(() => {
    if (projectsStore.currentToken) {
      onProjectChange()
    }
  })
})

onUnmounted(() => {
  store.stopPolling()
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 dark:bg-gray-950 text-gray-900 dark:text-gray-100 p-6 md:p-10 font-sans">
    <header class="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-8 border-b border-gray-200 dark:border-gray-800 pb-6">
      <div>
        <h1 class="text-3xl font-bold text-blue-500 dark:text-blue-500 tracking-tight">TgMetrics</h1>
        <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">Панель управления аналитикой</p>
      </div>

      <div class="flex flex-wrap items-center gap-3 w-full lg:w-auto">
        <select
          v-if="projectsStore.projects.length > 1"
          :value="projectsStore.currentToken"
          @change="projectsStore.selectProject(($event.target as HTMLSelectElement).value); onProjectChange()"
          class="bg-white dark:bg-gray-900 border border-gray-300 dark:border-gray-700 focus:border-blue-500 text-sm rounded-full px-4 py-2 outline-none text-gray-800 dark:text-gray-200"
        >
          <option v-for="p in projectsStore.projects" :key="p.project_token" :value="p.project_token">
            {{ p.name }}
          </option>
        </select>
        <span v-else-if="projectsStore.currentProject" class="text-sm font-medium text-gray-700 dark:text-gray-300 px-1">
          {{ projectsStore.currentProject.name }}
        </span>

        <button
          @click="openCreateModal"
          class="bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 text-sm font-medium px-4 py-2 rounded-full transition active:scale-95 text-gray-700 dark:text-gray-300"
        >
          + Проект
        </button>

        <button
          @click="themeStore.cycle()"
          class="bg-gray-200 dark:bg-gray-800 hover:bg-gray-300 dark:hover:bg-gray-700 text-sm font-medium px-4 py-2 rounded-full transition active:scale-95 text-gray-700 dark:text-gray-300"
          :title="`Тема: ${themeStore.mode}`"
        >
          {{ themeIcon }} Тема
        </button>

        <template v-if="projectsStore.currentToken">
          <button
            @click="onCustomToggle"
            class="font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95"
            :class="
              store.periodPreset === null
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
                : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700'
            "
          >
            Кастом
          </button>

          <div v-if="showDatePicker" class="w-64">
            <VueDatePicker
              v-model="store.dateRange"
              @update:model-value="onCustomDateChange"
              range
              :dark="themeStore.isDark"
              :enable-time-picker="false"
              auto-apply
              placeholder="Выберите период"
            />
          </div>

          <button
            v-for="preset in periodPresets"
            :key="preset.id"
            @click="onPreset(preset.id)"
            class="font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95"
            :class="
              store.periodPreset === preset.id
                ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20'
                : 'bg-white dark:bg-gray-800 hover:bg-gray-50 dark:hover:bg-gray-700 text-gray-700 dark:text-gray-300 border border-gray-300 dark:border-gray-700'
            "
          >
            {{ preset.label }}
          </button>

          <button
            @click="loadData"
            class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-5 py-2.5 rounded-full transition active:scale-95 shadow-lg shadow-blue-500/20"
          >
            Обновить
          </button>
        </template>
      </div>
    </header>

    <div v-if="!projectsStore.loading && !projectsStore.projects.length" class="flex flex-col items-center justify-center py-32 gap-4">
      <p class="text-lg text-gray-500 dark:text-gray-400">У вас пока нет проектов</p>
      <button
        @click="openCreateModal"
        class="bg-blue-600 hover:bg-blue-500 text-white font-medium text-sm px-6 py-2.5 rounded-full transition active:scale-95 shadow-lg shadow-blue-500/20"
      >
        Создать проект
      </button>
    </div>

    <div v-else-if="store.loading && !store.financials" class="flex justify-center items-center py-32 text-gray-400 dark:text-gray-500">
      <span class="animate-pulse text-lg">Загрузка метрик...</span>
    </div>

    <div v-else class="space-y-6">
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7 gap-4" v-if="store.financials">
        <StatCard title="Выручка" :value="formatNumber(store.financials.total_revenue)" :delta="d('total_revenue')" />
        <StatCard title="MRR" :value="formatNumber(store.financials.mrr)" :delta="d('mrr')" />
        <StatCard title="ARR" :value="formatNumber(store.financials.arr)" :delta="d('arr')" />
        <StatCard title="ARPPU" :value="formatNumber(store.financials.arppu)" :delta="d('arppu')" />
        <StatCard title="Активные подписки" :value="store.financials.active_subscriptions" :delta="d('active_subscriptions')" />
        <StatCard title="Прогнозный LTV" :value="formatNumber(store.financials.forecast_ltv)" :delta="d('forecast_ltv')" />
        <StatCard title="Соотношение с CAC" :value="formatRatio(store.financials.ltv_cac_ratio)" accent="green" :delta="d('ltv_cac_ratio')" />
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <ActivityChart
          :data="store.activityData"
          :granularity="store.activityGranularity"
          @update:granularity="onGranularityChange"
        />

        <FunnelChart
          :data="store.funnelData"
          :project-token="projectsStore.currentToken"
        />
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" v-if="store.financials">
        <StatCard title="CR1 (Первый платеж)" :value="`${store.financials.cr_first}%`" :delta="d('cr_first')" />
        <StatCard title="CR2 (Повторный платеж)" :value="`${store.financials.cr_repeat}%`" :delta="d('cr_repeat')" />
        <StatCard title="Churn Rate, %" :value="`${store.financials.churn_rate}%`" :delta="d('churn_rate')" invert-delta />
        <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-5 rounded-xl h-full flex flex-col min-h-[104px]">
          <span class="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">Вид оттока</span>
          <select
            class="bg-gray-100 dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-200 rounded-lg px-3 py-2 mt-2 w-full border border-gray-300 dark:border-gray-700 focus:outline-none focus:border-blue-500"
          >
            <option selected>по подписке</option>
            <option disabled>по активности</option>
            <option disabled>по платежам</option>
          </select>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SubscriptionStatuses />
        <TrafficTable :data="store.trafficMetrics" :project-token="projectsStore.currentToken" />
      </div>

      <ProductMappings :project-token="projectsStore.currentToken" />

      <RetentionTable :data="store.retentionData" />
    </div>

    <div v-if="showCreateModal" class="fixed inset-0 bg-black/60 flex items-center justify-center p-4 z-50" @click.self="closeCreateModal">
      <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 rounded-xl p-6 w-full max-w-md space-y-4">
        <h2 class="text-lg font-semibold text-gray-900 dark:text-gray-100">Новый проект</h2>

        <template v-if="!projectsStore.createdProject">
          <input
            v-model="newProjectName"
            @keyup.enter="createProject"
            type="text"
            placeholder="Название проекта"
            class="w-full bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 focus:border-blue-500 text-sm rounded-lg px-4 py-2.5 outline-none text-gray-900 dark:text-gray-100 placeholder-gray-400 dark:placeholder-gray-500"
          />
          <p v-if="projectsStore.error" class="text-sm text-red-500">{{ projectsStore.error }}</p>
          <div class="flex justify-end gap-2">
            <button
              @click="closeCreateModal"
              class="text-sm px-4 py-2 rounded-lg text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition"
            >
              Отмена
            </button>
            <button
              @click="createProject"
              :disabled="!newProjectName.trim()"
              class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
            >
              Создать
            </button>
          </div>
        </template>

        <template v-else>
          <p class="text-sm text-gray-600 dark:text-gray-300">
            Проект «{{ projectsStore.createdProject.name }}» создан. Токен для подключения бота:
          </p>
          <code class="block bg-gray-100 dark:bg-gray-800 border border-gray-300 dark:border-gray-700 rounded-lg px-4 py-3 text-sm text-blue-600 dark:text-blue-400 font-mono break-all select-text">
            {{ projectsStore.createdProject.project_token }}
          </code>
          <div class="flex justify-end gap-2">
            <button
              @click="copyToken"
              class="text-sm px-4 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 border border-gray-300 dark:border-gray-700 transition"
            >
              Скопировать
            </button>
            <button
              @click="closeCreateModal"
              class="bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium px-5 py-2 rounded-lg transition-colors"
            >
              Готово
            </button>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>
