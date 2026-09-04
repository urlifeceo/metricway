<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  LineController,
  type Plugin
} from 'chart.js'
import { useThemeStore } from '@/stores/theme'
import type { ActivityPoint, ActivityGranularity } from '@/types/analytics'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  LineController
)

const props = withDefaults(
  defineProps<{
    data?: ActivityPoint[]
    granularity?: ActivityGranularity
  }>(),
  {
    data: () => [],
    granularity: 'dau'
  }
)

const emit = defineEmits<{
  (e: 'update:granularity', value: ActivityGranularity): void
}>()

const themeStore = useThemeStore()

const modes: Array<{ id: ActivityGranularity; label: string }> = [
  { id: 'dau', label: 'DAU' },
  { id: 'wau', label: 'WAU' },
  { id: 'mau', label: 'MAU' }
]

const lineGlow: Plugin = {
  id: 'lineGlow',
  beforeDatasetsDraw(chart) {
    chart.ctx.save()
    chart.ctx.shadowBlur = 12
    chart.ctx.shadowColor = 'rgba(59, 130, 246, 0.7)'
  },
  afterDatasetsDraw(chart) {
    chart.ctx.restore()
  }
}

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS | null = null

function renderChart() {
  if (!canvasRef.value) return

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  if (!props.data || props.data.length === 0) return

  const label = modes.find(m => m.id === props.granularity)?.label ?? 'DAU'
  const isDark = themeStore.isDark
  const gridColor = isDark ? 'rgba(31, 41, 55, 0.6)' : 'rgba(229, 231, 235, 0.9)'
  const tickColor = isDark ? '#6b7280' : '#4b5563'
  const tooltipBg = isDark ? '#111827' : '#ffffff'
  const tooltipBorder = isDark ? '#1f2937' : '#e5e7eb'

  chartInstance = new ChartJS(canvasRef.value, {
    type: 'line',
    data: {
      labels: props.data.map(i => i.date),
      datasets: [
        {
          label: `${label} (Active Users)`,
          backgroundColor: '#3b82f6',
          borderColor: '#3b82f6',
          data: props.data.map(i => i.value),
          tension: 0.4,
          pointRadius: 0,
          pointHoverRadius: 4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: {
        mode: 'index',
        intersect: false
      },
      plugins: {
        legend: {
          labels: {
            boxWidth: 12,
            color: tickColor
          }
        },
        tooltip: {
          backgroundColor: tooltipBg,
          borderColor: tooltipBorder,
          borderWidth: 1,
          titleColor: isDark ? '#9ca3af' : '#6b7280',
          bodyColor: isDark ? '#ffffff' : '#111827',
          padding: 10,
          displayColors: false,
          callbacks: {
            label: (context) => `${context.parsed.y} юзеров`
          }
        }
      },
      scales: {
        x: {
          ticks: { color: tickColor, maxTicksLimit: 12 },
          grid: { color: gridColor }
        },
        y: {
          beginAtZero: true,
          ticks: { color: tickColor },
          grid: { color: gridColor }
        }
      }
    },
    plugins: [lineGlow]
  })
}

onMounted(() => {
  renderChart()
})

watch(
  () => [props.data, themeStore.isDark] as const,
  () => {
    renderChart()
  },
  { deep: true }
)

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.destroy()
  }
})
</script>

<template>
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-6 rounded-xl">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-semibold text-gray-900 dark:text-gray-200">Динамика активности</h2>
      <div class="flex items-center gap-3 text-sm">
        <button
          v-for="mode in modes"
          :key="mode.id"
          @click="emit('update:granularity', mode.id)"
          class="pb-0.5 transition-colors"
          :class="
            granularity === mode.id
              ? 'text-blue-500 dark:text-blue-400 border-b border-blue-500 dark:border-blue-400 font-medium'
              : 'text-gray-400 hover:text-gray-600 dark:hover:text-gray-200'
          "
        >
          {{ mode.label }}
        </button>
      </div>
    </div>
    <div class="h-64 relative">
      <canvas ref="canvasRef" v-show="props.data && props.data.length > 0"></canvas>
      <div
        v-if="!props.data || props.data.length === 0"
        class="h-full flex items-center justify-center text-gray-400 dark:text-gray-500 text-sm"
      >
        Нет данных для отображения
      </div>
    </div>
  </div>
</template>
