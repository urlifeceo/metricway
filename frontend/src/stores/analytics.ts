import { defineStore } from 'pinia'
import api from '@/api'
import type {
  CohortRetention,
  FunnelStep,
  FinancialMetrics,
  UTMMetric,
  DAUPoint
} from '@/types/analytics'

export const useAnalyticsStore = defineStore('analytics', {
  state: () => ({
    dateRange: [
      new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      new Date()
    ] as [Date, Date],

    dauData: [] as DAUPoint[],
    financials: null as FinancialMetrics | null,
    utmMetrics: [] as UTMMetric[],
    retentionData: [] as CohortRetention[],
    funnelData: [] as FunnelStep[],
    availableEvents: [] as string[],

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

    async fetchAll(projectToken: string, steps?: string[]) {
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

        let targetSteps = steps
        if (!targetSteps?.length) {
          if (!this.availableEvents.length) {
            await this.fetchAvailableEvents(projectToken)
          }
          targetSteps = this.availableEvents.slice(0, 3)
        }

        const [
          dauRes,
          finRes,
          utmRes,
          retentionRes,
          funnelRes
        ] = await Promise.all([
          api.get('/analytics/dau', { params }),
          api.get('/analytics/financials', { params }),
          api.get('/analytics/utm', { params }),
          api.get('/analytics/retention', { params }),
          targetSteps.length
            ? api.get('/analytics/funnel', {
                params: { ...params, steps: targetSteps },
                paramsSerializer: { indexes: null }
              })
            : Promise.resolve({ data: [] })
        ])

        this.dauData = dauRes.data
        this.financials = finRes.data
        this.utmMetrics = utmRes.data
        this.retentionData = retentionRes.data
        this.funnelData = funnelRes.data
      } catch (err) {
        this.error = 'Failed to fetch analytics'
      } finally {
        this.loading = false
      }
    },

    startPolling(projectToken: string, intervalMs = 10000, steps?: string[]) {
      this.stopPolling()
      this.fetchAll(projectToken, steps)
      this.timer = setInterval(() => {
        this.fetchAll(projectToken, steps)
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