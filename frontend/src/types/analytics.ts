export type ActivityGranularity = 'dau' | 'wau' | 'mau'

export interface ActivityPoint {
  date: string
  value: number
}

export interface FinancialMetrics {
  total_revenue: number
  paying_users: number
  total_users: number
  arpu: number
  arppu: number
  conversion_rate: number
  mrr: number
  arr: number
  active_subscriptions: number
  churn_rate: number
  forecast_ltv: number
  ltv_cac_ratio: number
  cr_first: number
  cr_repeat: number
}

export interface TrafficMetric {
  source: string
  acquisitions: number
  buyers: number
  conversion_rate: number
  spend: number
  cac: number
}

export interface CohortRetention {
  cohort_date: string
  cohort_size: number
  retention: Record<number, number>
}

export interface FunnelStep {
  step_name: string
  users_count: number
  conversion_rate: number
}
