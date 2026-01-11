from pydantic import BaseModel, Field
from typing import List, Optional


class UserStatsResponse(BaseModel):
    """Overall user statistics"""
    total_sessions: int = Field(..., description="Total number of sessions created")
    total_test_cases: int = Field(..., description="Total test cases generated")
    total_functional: int = Field(..., description="Total functional test cases")
    total_negative: int = Field(..., description="Total negative test cases")
    total_boundary: int = Field(..., description="Total boundary test cases")
    avg_execution_time_ms: int = Field(..., description="Average execution time in milliseconds")
    most_used_model: Optional[str] = Field(None, description="Most frequently used model")
    sessions_last_30_days: int = Field(..., description="Sessions created in last 30 days")


class TimelineDataPoint(BaseModel):
    """Single data point in timeline"""
    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    count: int = Field(..., description="Number of sessions on this date")


class TimelineResponse(BaseModel):
    """Timeline data for charting sessions over time"""
    timeline: List[TimelineDataPoint]
    days: int = Field(..., description="Number of days covered")


class ModelUsageDataPoint(BaseModel):
    """Single model usage data point"""
    model: str = Field(..., description="Model name")
    count: int = Field(..., description="Number of times used")


class ModelUsageResponse(BaseModel):
    """Breakdown of sessions by model"""
    model_usage: List[ModelUsageDataPoint]


class TestCaseBreakdownResponse(BaseModel):
    """Breakdown of test cases by type"""
    functional: int = Field(..., description="Number of functional test cases")
    negative: int = Field(..., description="Number of negative test cases")
    boundary: int = Field(..., description="Number of boundary test cases")
