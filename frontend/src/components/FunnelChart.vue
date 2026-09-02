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

    <div v-if="data && data.length" class="space-y-4 pt-2">
      <div v-for="(step, idx) in data" :key="step.step_name" class="relative">
        <div class="flex justify-between text-sm font-medium mb-1">
          <span class="text-gray-200">{{ idx + 1 }}. {{ step.step_name }}</span>
          <span class="text-gray-400">
            {{ step.users_count }} юз. ({{ step.conversion_rate }}%)
          </span>
        </div>
        <div class="w-full bg-gray-800 h-2 rounded-full overflow-hidden">
          <div
            class="bg-blue-500 h-full rounded-full transition-all duration-500"
            :style="{ width: step.conversion_rate + '%' }"
          ></div>
        </div>
      </div>
    </div>

    <div v-else class="text-center text-sm text-gray-500 py-8">
      Нет данных по выбранным шагам
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'

const props = defineProps<{
  data: Array<{ step_name: string; users_count: number; conversion_rate: number }>
  projectToken: string
}>()

const analyticsStore = useAnalyticsStore()

const currentSteps = ref<string[]>([])
const selectedEventToAdd = ref('')

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