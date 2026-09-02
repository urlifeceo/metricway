from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class DAUResponse(BaseModel):
    date: date
    dau: int


class ActivityPoint(BaseModel):
    date: date
    value: int


class FinancialMetricsResponse(BaseModel):
    total_revenue: float
    paying_users: int
    total_users: int
    arpu: float
    arppu: float
    conversion_rate: float
    mrr: float
    arr: float
    active_subscriptions: int
    churn_rate: float
    forecast_ltv: float
    ltv_cac_ratio: float
    cr_first: float
    cr_repeat: float


class UTMMetric(BaseModel):
    source: str
    campaign: str
    acquisitions: int
    buyers: int
    revenue: float
    conversion_rate: float


class TrafficMetric(BaseModel):
    source: str
    acquisitions: int
    buyers: int
    conversion_rate: float
    spend: float
    cac: float


class TrafficSpendRequest(BaseModel):
    project_token: str
    source: str
    spend: float

class CohortRetention(BaseModel):
    cohort_date: str
    cohort_size: int
    retention: dict[int, float]

class FunnelStep(BaseModel):
    step_name: str
    users_count: int
    conversion_rate: float