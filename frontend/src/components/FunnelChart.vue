<template>
  <div class="bg-gray-900 p-6 rounded-xl border border-gray-800 space-y-5">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <h3 class="text-base font-semibold text-gray-200">Воронка конверсии</h3>

      <div v-if="analyticsStore.availableEvents.length" class="flex items-center gap-2">
        <select
          v-model="selectedEventToAdd"
          class="bg-gray-800 text-sm text-gray-200 rounded-lg px-3 py-1.5 border border-gray-700 focus:outline-none focus:border-blue-500"
        >
          <option value="" disabled selected>Добавить шаг...</option>
          <option
            v-for="event in unusedEvents"
            :key="event"
            :value="event"
          >
            {{ event }}
          </option>
        </select>
        <button
          @click="addStep"
          :disabled="!selectedEventToAdd"
          class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium rounded-lg transition-colors"
        >
          +
        </button>
      </div>
    </div>

    <div v-if="currentSteps.length" class="flex flex-wrap gap-2">
      <div
        v-for="(step, idx) in currentSteps"
        :key="step"
        class="flex items-center gap-1.5 bg-gray-800 text-gray-300 text-xs px-2.5 py-1 rounded-md border border-gray-700"
      >
        <span>{{ idx + 1 }}. {{ step }}</span>
        <button
          @click="removeStep(idx)"
          class="text-gray-400 hover:text-red-400 font-bold ml-1"
        >
          ×
        </button>
      </div>
    </div>

    <template v-if="data && data.length">
      <svg
        :viewBox="`0 0 ${SVG_W} ${funnelHeight}`"
        class="w-full max-w-2xl mx-auto"
        role="img"
      >
        <defs>
          <linearGradient id="funnelGrad" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stop-color="#1d4ed8" />
            <stop offset="100%" stop-color="#60a5fa" />
          </linearGradient>
        </defs>

        <g v-for="(seg, idx) in segments" :key="idx">
          <polygon
            :points="seg.points"
            fill="url(#funnelGrad)"
            opacity="0.9"
          />
          <text
            v-if="seg.textInside"
            :x="CX"
            :y="seg.centerY + 4"
            text-anchor="middle"
            fill="#ffffff"
            font-size="12"
            font-weight="600"
          >
            {{ seg.users }} юз.
          </text>
          <text
            :x="RIGHT_X"
            :y="seg.centerY - 2"
            fill="#e5e7eb"
            font-size="12"
            font-weight="600"
          >
            {{ seg.users }} юз.
          </text>
          <text
            :x="RIGHT_X"
            :y="seg.centerY + 12"
            fill="#9ca3af"
            font-size="10"
          >
            {{ seg.pctFirst }}% от начала
          </text>
        </g>
      </svg>

      <div class="space-y-4 pt-2">
        <template v-for="(step, idx) in data" :key="step.step_name">
          <div
            v-if="idx > 0"
            class="flex items-center gap-2 text-xs text-gray-500 pl-1"
          >
            <span class="text-gray-600">↓</span>
            <span :class="stepDropClass(step, idx)">
              {{ stepDrop(step, idx) }}
            </span>
            <span>к предыдущему шагу</span>
          </div>

          <div>
            <div class="flex justify-between text-sm font-medium mb-1">
              <span class="text-gray-200">{{ idx + 1 }}. {{ step.step_name }}</span>
              <span class="text-gray-400">
                {{ step.users_count }} юз. ({{ step.conversion_rate }}%)
              </span>
            </div>
            <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full transition-all duration-500 bg-gradient-to-r from-blue-600 to-blue-400"
                :style="{ width: step.conversion_rate + '%' }"
              ></div>
            </div>
          </div>
        </template>
      </div>
    </template>

    <div v-else class="text-center text-sm text-gray-500 py-8">
      Нет данных по выбранным шагам
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import type { FunnelStep } from '@/types/analytics'

const props = defineProps<{
  data: FunnelStep[]
  projectToken: string
}>()

const analyticsStore = useAnalyticsStore()

const currentSteps = ref<string[]>([])
const selectedEventToAdd = ref('')

const SVG_W = 720
const CX = 260
const RIGHT_X = 560
const MAX_W = 500
const MIN_W = 110
const SEG_H = 46

const firstUsers = computed(() => props.data?.[0]?.users_count ?? 0)

const segments = computed(() => {
  const rows = props.data
  if (!rows?.length || firstUsers.value <= 0) return []

  return rows.map((step, idx) => {
    const ratio = Math.min(step.users_count / firstUsers.value, 1)
    const topW = MIN_W + (MAX_W - MIN_W) * ratio

    const next = rows[idx + 1]
    const nextRatio = next
      ? Math.min(next.users_count / firstUsers.value, 1)
      : ratio
    const bottomW = MIN_W + (MAX_W - MIN_W) * nextRatio

    const yTop = idx * SEG_H
    const yBottom = yTop + SEG_H - 4

    const points = [
      [CX - topW / 2, yTop],
      [CX + topW / 2, yTop],
      [CX + bottomW / 2, yBottom],
      [CX - bottomW / 2, yBottom]
    ]
      .map(([x, y]) => `${x},${y}`)
      .join(' ')

    return {
      points,
      centerY: yTop + SEG_H / 2,
      users: step.users_count,
      pctFirst: step.conversion_rate,
      textInside: topW >= 100
    }
  })
})

const funnelHeight = computed(() => Math.max(SEG_H * (props.data?.length ?? 0), SEG_H))

function stepDrop(step: FunnelStep, idx: number): string {
  const prev = props.data[idx - 1]
  if (!prev || prev.users_count === 0) return '—'
  const change = ((step.users_count - prev.users_count) / prev.users_count) * 100
  const sign = change >= 0 ? '+' : '−'
  return `${sign}${Math.abs(change).toFixed(2)}%`
}

function stepDropClass(step: FunnelStep, idx: number): string {
  const prev = props.data[idx - 1]
  if (!prev || prev.users_count === 0) return 'text-gray-600'
  const change = step.users_count - prev.users_count
  return change >= 0 ? 'text-emerald-400' : 'text-red-400'
}

const unusedEvents = computed(() => {
  return analyticsStore.availableEvents.filter(e => !currentSteps.value.includes(e))
})

const addStep = () => {
  if (!selectedEventToAdd.value) return
  currentSteps.value.push(selectedEventToAdd.value)
  selectedEventToAdd.value = ''
  updateFunnel()
}

const removeStep = (index: number) => {
  currentSteps.value.splice(index, 1)
  updateFunnel()
}

const updateFunnel = () => {
  if (props.projectToken) {
    analyticsStore.fetchAll(props.projectToken, currentSteps.value)
  }
}

watch(
  () => props.data,
  (newData) => {
    if (newData && newData.length && currentSteps.value.length === 0) {
      currentSteps.value = newData.map(s => s.step_name)
    }
  },
  { immediate: true }
)
</script>
