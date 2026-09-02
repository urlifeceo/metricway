import { defineStore } from 'pinia'
import api from '@/api'
import type {
  CohortRetention,
  FunnelStep,
  FinancialMetrics,
  TrafficMetric,
  ActivityPoint,
  ActivityGranularity
} from '@/types/analytics'

export const useAnalyticsStore = defineStore('analytics', {
  state: () => ({
    dateRange: [
      new Date(Date.now() - 30 * 24 * 60 * 60 * 1000),
      new Date()
    ] as [Date, Date],

    activityGranularity: 'dau' as ActivityGranularity,
    activityData: [] as ActivityPoint[],
    financials: null as FinancialMetrics | null,
    trafficMetrics: [] as TrafficMetric[],
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
          activityRes,
          finRes,
          trafficRes,
          retentionRes,
          funnelRes
        ] = await Promise.all([
          api.get('/analytics/activity', {
            params: { ...params, granularity: this.activityGranularity }
          }),
          api.get('/analytics/financials', { params }),
          api.get('/analytics/traffic', { params }),
          api.get('/analytics/retention', {
            params: { ...params, unit: 'month' }
          }),
          targetSteps.length
            ? api.get('/analytics/funnel', {
                params: { ...params, steps: targetSteps },
                paramsSerializer: { indexes: null }
              })
            : Promise.resolve({ data: [] })
        ])

        this.activityData = activityRes.data
        this.financials = finRes.data
        this.trafficMetrics = trafficRes.data
        this.retentionData = retentionRes.data
        this.funnelData = funnelRes.data
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

    setGranularity(granularity: ActivityGranularity) {
      this.activityGranularity = granularity
    },

    setPeriodPreset(preset: 'this_month' | 'prev_month') {
      const now = new Date()
      if (preset === 'this_month') {
        this.dateRange = [new Date(now.getFullYear(), now.getMonth(), 1), now]
      } else {
        this.dateRange = [
          new Date(now.getFullYear(), now.getMonth() - 1, 1),
          new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59)
        ]
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
