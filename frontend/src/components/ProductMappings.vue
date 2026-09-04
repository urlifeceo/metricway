<script setup lang="ts">
import { ref } from 'vue'
import { useAnalyticsStore } from '@/stores/analytics'
import type { BillingType } from '@/types/analytics'

defineProps<{
  projectToken: string | null
}>()

const store = useAnalyticsStore()

const billingTypes: Array<{ id: BillingType; label: string }> = [
  { id: 'monthly', label: 'Месячная подписка' },
  { id: 'yearly', label: 'Годовая подписка' },
  { id: 'one_time', label: 'Разовая покупка' }
]

const selectedTypes = ref<Record<string, BillingType>>({})

function selectType(productId: string, billingType: BillingType) {
  selectedTypes.value[productId] = billingType
}

function saveMapping(projectToken: string | null, productId: string) {
  if (!projectToken) return
  const billingType = selectedTypes.value[productId]
  if (!billingType) return
  store.saveProductMapping(projectToken, productId, billingType)
  delete selectedTypes.value[productId]
}
</script>

<template>
  <div class="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-800 p-6 rounded-xl">
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-base font-semibold text-gray-900 dark:text-gray-200">Продукты</h2>
      <span class="text-xs text-gray-500 dark:text-gray-500">Классификация для расчёта MRR / ARR / Churn</span>
    </div>

    <div v-if="!store.unknownProducts.length && !store.productMappings.length" class="text-sm text-gray-400 dark:text-gray-500 py-2">
      Нет данных о покупках
    </div>

    <div v-else class="space-y-4">
      <div v-if="store.unknownProducts.length">
        <div class="text-xs text-yellow-500 dark:text-yellow-400 uppercase tracking-wider mb-2">
          Неклассифицированные ({{ store.unknownProducts.length }})
        </div>
        <div class="space-y-2">
          <div
            v-for="product in store.unknownProducts"
            :key="product.product_id"
            class="flex flex-wrap items-center justify-between gap-3 bg-gray-50 dark:bg-gray-800/60 border border-gray-200 dark:border-gray-700 rounded-lg px-4 py-2.5"
          >
            <div class="min-w-0">
              <div class="text-sm text-gray-900 dark:text-gray-200 font-medium truncate">{{ product.product_id }}</div>
              <div class="text-xs text-gray-500 dark:text-gray-500">{{ product.payments_count }} платежей · последний {{ product.last_amount }}</div>
            </div>
            <div class="flex items-center gap-2">
              <select
                :value="selectedTypes[product.product_id] ?? ''"
                @change="selectType(product.product_id, ($event.target as HTMLSelectElement).value as BillingType)"
                class="bg-gray-100 dark:bg-gray-800 text-sm text-gray-900 dark:text-gray-200 rounded-lg px-3 py-1.5 border border-gray-300 dark:border-gray-700 focus:outline-none focus:border-blue-500"
              >
                <option value="" disabled selected>Выберите тип...</option>
                <option v-for="t in billingTypes" :key="t.id" :value="t.id">{{ t.label }}</option>
              </select>
              <button
                @click="saveMapping(projectToken, product.product_id)"
                :disabled="!selectedTypes[product.product_id]"
                class="bg-blue-600 hover:bg-blue-500 disabled:opacity-50 text-white text-sm font-medium px-4 py-1.5 rounded-lg transition-colors"
              >
                Сохранить
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-else class="text-sm text-emerald-500 dark:text-emerald-400">
        Все продукты классифицированы
      </div>

      <div v-if="store.productMappings.length">
        <div class="text-xs text-gray-500 dark:text-gray-500 uppercase tracking-wider mb-2">Классифицированные</div>
        <div class="flex flex-wrap gap-2">
          <div
            v-for="mapping in store.productMappings"
            :key="mapping.product_id"
            class="flex items-center gap-2 bg-gray-100 dark:bg-gray-800 text-xs px-2.5 py-1 rounded-md border border-gray-200 dark:border-gray-700"
          >
            <span class="text-gray-700 dark:text-gray-300">{{ mapping.product_id }}</span>
            <span
              class="px-1.5 py-0.5 rounded font-medium"
              :class="mapping.billing_type === 'monthly' ? 'bg-blue-500/20 text-blue-600 dark:text-blue-300' : mapping.billing_type === 'yearly' ? 'bg-indigo-500/20 text-indigo-600 dark:text-indigo-300' : 'bg-gray-500/20 text-gray-600 dark:text-gray-300'"
            >
              {{ billingTypes.find(t => t.id === mapping.billing_type)?.label ?? mapping.billing_type }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
