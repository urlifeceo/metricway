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
  LineController
} from 'chart.js'

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
    data?: { date: string; dau: number }[]
  }>(),
  {
    data: () => []
  }
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
let chartInstance: ChartJS | null = null

function renderChart() {
  if (!canvasRef.value) return

  if (chartInstance) {
    chartInstance.destroy()
    chartInstance = null
  }

  if (!props.data || props.data.length === 0) return

  chartInstance = new ChartJS(canvasRef.value, {
    type: 'line',
    data: {
      labels: props.data.map(i => i.date),
      datasets: [
        {
          label: 'DAU (Daily Active Users)',
          backgroundColor: '#3b82f6',
          borderColor: '#3b82f6',
          data: props.data.map(i => i.dau),
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false
    }
  })
}

onMounted(() => {
  renderChart()
})

watch(
  () => props.data,
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
  <div class="h-64 relative">
    <canvas ref="canvasRef" v-show="props.data && props.data.length > 0"></canvas>
    <div
      v-if="!props.data || props.data.length === 0"
      class="h-full flex items-center justify-center text-gray-500 text-sm"
    >
      Нет данных для отображения
    </div>
  </div>
</template>