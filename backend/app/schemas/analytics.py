from datetime import date
from typing import List, Optional
from pydantic import BaseModel


class DAUResponse(BaseModel):
    date: date
    dau: int


class FinancialMetricsResponse(BaseModel):
    total_revenue: float
    paying_users: int
    total_users: int
    arpu: float
    arppu: float
    conversion_rate: float


class UTMMetric(BaseModel):
    source: str
    campaign: str
    acquisitions: int
    buyers: int
    revenue: float
    conversion_rate: float
    
class CohortRetention(BaseModel):
    cohort_date: str
    cohort_size: int
    retention: dict[int, float]

class FunnelStep(BaseModel):
    step_name: str
    users_count: int
    conversion_rate: float