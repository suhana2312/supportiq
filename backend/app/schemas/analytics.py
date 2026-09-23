from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class DailyMetric(BaseModel):
    date: str
    count: int

class CategoryMetric(BaseModel):
    category: str
    count: int

class AnalyticsOverviewResponse(BaseModel):
    total_customers: int
    total_conversations: int
    open_tickets: int
    escalated_tickets: int
    total_documents: int
    ai_resolution_rate: float
    avg_response_time_seconds: float
    customer_satisfaction_score: float
    total_orders: int
    refund_requests: int

class AnalyticsTrendsResponse(BaseModel):
    conversations_trend: List[DailyMetric]
    tickets_trend: List[DailyMetric]
    ticket_categories: List[CategoryMetric]
    resolution_distribution: Dict[str, int]
    ratings_distribution: Dict[int, int]
