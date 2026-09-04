export type ActivityGranularity = 'dau' | 'wau' | 'mau'

export type PeriodPreset = 'this_month' | 'last_3_months' | 'this_year'

export type BillingType = 'monthly' | 'yearly' | 'one_time'

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

export interface FunnelStepConfig {
  event: string
  label: string
}

export interface ProductMapping {
  product_id: string
  billing_type: BillingType
}

export interface UnknownProduct {
  product_id: string
  payments_count: number
  last_amount: number
}
