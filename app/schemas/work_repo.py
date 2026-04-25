from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class WorkRepoCreate(BaseModel):
    w_date: date
    w_title: str = Field(..., max_length=20)
    content: Optional[str] = None


class WorkRepoUpdate(BaseModel):
    w_date: Optional[date] = None
    w_title: Optional[str] = Field(None, max_length=20)
    content: Optional[str] = None


class WorkRepoOut(BaseModel):
    w_id: int
    w_date: date
    w_title: str
    u_id: int
    content: Optional[str] = None
    create_time: datetime
    update_time: datetime
    is_del: int

    model_config = {"from_attributes": True}
