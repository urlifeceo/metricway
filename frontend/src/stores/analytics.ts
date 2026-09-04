import { defineStore } from 'pinia'
import api from '@/api'
import type {
  CohortRetention,
  FunnelStep,
  FunnelStepConfig,
  FinancialMetrics,
  TrafficMetric,
  ActivityPoint,
  ActivityGranularity,
  PeriodPreset,
  ProductMapping,
  UnknownProduct
} from '@/types/analytics'

function shiftRangeBack([from, to]: [Date, Date]): [Date, Date] {
  const duration = to.getTime() - from.getTime()
  return [new Date(from.getTime() - duration - 1), new Date(to.getTime() - 1)]
}

function normalizeRangeStart(date: Date): Date {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

function normalizeRangeEnd(date: Date): Date {
  const d = new Date(date)
  d.setHours(23, 59, 59, 999)
  return d
}

export const useAnalyticsStore = defineStore('analytics', {
  state: () => ({
    dateRange: [
      new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      new Date()
    ] as [Date, Date],
    periodPreset: null as PeriodPreset | null,

    activityGranularity: 'dau' as ActivityGranularity,
    activityData: [] as ActivityPoint[],
    financials: null as FinancialMetrics | null,
    financialsPrev: null as FinancialMetrics | null,
    trafficMetrics: [] as TrafficMetric[],
    retentionData: [] as CohortRetention[],
    funnelData: [] as FunnelStep[],
    funnelSteps: [] as FunnelStepConfig[],
    availableEvents: [] as string[],
    productMappings: [] as ProductMapping[],
    unknownProducts: [] as UnknownProduct[],

    loading: false,
    error: null as string | null,
    timer: null as ReturnType<typeof setInterval> | null
  }),

  actions: {
    async fetchAvailableEvents(projectToken: string): Promise<string[]> {
      try {
        const res = await api.get('/analytics/funnel/events', {
          params: { project_token: projectToken }
        })
        this.availableEvents = res.data
        return res.data
      } catch (err) {
        this.error = 'Failed to load events'
        return []
      }
    },

    async fetchFunnelConfig(projectToken: string) {
      try {
        const res = await api.get('/analytics/funnel/config', {
          params: { project_token: projectToken }
        })
        this.funnelSteps = res.data.steps ?? []
      } catch (err) {
        this.error = 'Failed to load funnel config'
      }
    },

    async updateFunnelSteps(projectToken: string, steps: FunnelStepConfig[]) {
      this.funnelSteps = steps
      try {
        await api.put('/analytics/funnel/config', {
          project_token: projectToken,
          steps
        })
      } catch (err) {
        this.error = 'Failed to save funnel config'
      }
      await this.fetchAll(projectToken)
    },

    async fetchAll(projectToken: string) {
      if (!this.timer) {
        this.loading = true
      }
      this.error = null

      try {
        const [fromDate, toDate] = this.dateRange

        const params = {
          project_token: projectToken,
          from_date: fromDate.toISOString(),
          to_date: toDate.toISOString()
        }

        const prevRange = shiftRangeBack(this.dateRange)
        const prevParams = {
          project_token: projectToken,
          from_date: prevRange[0].toISOString(),
          to_date: prevRange[1].toISOString()
        }

        const funnelEvents = this.funnelSteps.map(s => s.event)

        const [
          activityRes,
          finRes,
          finPrevRes,
          trafficRes,
          retentionRes,
          funnelRes,
          productsRes,
          unknownProductsRes
        ] = await Promise.all([
          api.get('/analytics/activity', {
            params: { ...params, granularity: this.activityGranularity }
          }),
          api.get('/analytics/financials', { params }),
          api.get('/analytics/financials', { params: prevParams }),
          api.get('/analytics/traffic', { params }),
          api.get('/analytics/retention', {
            params: { ...params, unit: 'month' }
          }),
          funnelEvents.length
            ? api.get('/analytics/funnel', {
                params: { ...params, steps: funnelEvents },
                paramsSerializer: { indexes: null }
              })
            : Promise.resolve({ data: [] }),
          api.get('/analytics/products', {
            params: { project_token: projectToken }
          }),
          api.get('/analytics/products/unknown', {
            params: { project_token: projectToken }
          })
        ])

        this.activityData = activityRes.data
        this.financials = finRes.data
        this.financialsPrev = finPrevRes.data
        this.trafficMetrics = trafficRes.data
        this.retentionData = retentionRes.data
        this.funnelData = funnelRes.data
        this.productMappings = productsRes.data
        this.unknownProducts = unknownProductsRes.data
      } catch (err) {
        this.error = 'Failed to fetch analytics'
      } finally {
        this.loading = false
      }
    },

    async fetchTraffic(projectToken: string) {
      try {
        const [fromDate, toDate] = this.dateRange
        const res = await api.get('/analytics/traffic', {
          params: {
            project_token: projectToken,
            from_date: fromDate.toISOString(),
            to_date: toDate.toISOString()
          }
        })
        this.trafficMetrics = res.data
      } catch (err) {
        this.error = 'Failed to fetch traffic'
      }
    },

    async saveTrafficSpend(projectToken: string, source: string, spend: number) {
      try {
        await api.put('/analytics/traffic/spend', {
          project_token: projectToken,
          source,
          spend
        })
        await this.fetchTraffic(projectToken)
      } catch (err) {
        this.error = 'Failed to save spend'
      }
    },

    async saveProductMapping(projectToken: string, productId: string, billingType: string) {
      try {
        await api.put('/analytics/products', {
          project_token: projectToken,
          product_id: productId,
          billing_type: billingType
        })
        const [productsRes, unknownRes, finRes] = await Promise.all([
          api.get('/analytics/products', {
            params: { project_token: projectToken }
          }),
          api.get('/analytics/products/unknown', {
            params: { project_token: projectToken }
          }),
          api.get('/analytics/financials', {
            params: {
              project_token: projectToken,
              from_date: this.dateRange[0].toISOString(),
              to_date: this.dateRange[1].toISOString()
            }
          })
        ])
        this.productMappings = productsRes.data
        this.unknownProducts = unknownRes.data
        this.financials = finRes.data
      } catch (err) {
        this.error = 'Failed to save product mapping'
      }
    },

    setGranularity(granularity: ActivityGranularity) {
      this.activityGranularity = granularity
    },

    setDateRange(range: [Date, Date]) {
      this.dateRange = [normalizeRangeStart(range[0]), normalizeRangeEnd(range[1])]
    },

    setPeriodPreset(preset: PeriodPreset) {
      const now = new Date()
      if (preset === 'this_month') {
        this.dateRange = [new Date(now.getFullYear(), now.getMonth(), 1), now]
      } else if (preset === 'last_3_months') {
        this.dateRange = [
          new Date(now.getFullYear(), now.getMonth() - 3, now.getDate()),
          now
        ]
      } else {
        this.dateRange = [new Date(now.getFullYear(), 0, 1), now]
      }
      this.periodPreset = preset
    },

    startPolling(projectToken: string, intervalMs = 10000) {
      this.stopPolling()
      this.fetchAll(projectToken)
      this.timer = setInterval(() => {
        this.fetchAll(projectToken)
      }, intervalMs)
    },

    stopPolling() {
      if (this.timer) {
        clearInterval(this.timer)
        this.timer = null
      }
    }
  }
})
