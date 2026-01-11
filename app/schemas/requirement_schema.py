from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class RequirementBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=500, description="Requirement title")
    description: str = Field(..., min_length=1, description="Detailed requirement description")
    tags: Optional[str] = Field(None, max_length=500, description="Comma-separated tags")
    is_template: bool = Field(False, description="Mark as reusable template")


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1)
    tags: Optional[str] = Field(None, max_length=500)
    is_template: Optional[bool] = None


class RequirementResponse(RequirementBase):
    id: int
    user_id: int
    usage_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequirementListResponse(BaseModel):
    requirements: List[RequirementResponse]
    total: int
    skip: int
    limit: int
