export interface DAUPoint {
  date: string
  dau: number
}

export interface FinancialMetrics {
  total_revenue: number
  paying_users: number
  total_users: number
  arpu: number
  arppu: number
  conversion_rate: number
}

export interface UTMMetric {
  source: string
  campaign: string
  acquisitions: number
  buyers: number
  revenue: number
  conversion_rate: number
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
