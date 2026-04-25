from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field


class WorkRepoSumCreate(BaseModel):
    ws_date: date
    ws_title: str = Field(..., max_length=40)
    content: Optional[str] = None


class WorkRepoSumUpdate(BaseModel):
    ws_title: Optional[str] = Field(None, max_length=40)
    content: Optional[str] = None


class WorkRepoSumOut(BaseModel):
    ws_id: int
    ws_date: date
    ws_title: str
    content: Optional[str] = None
    create_time: datetime
    is_del: int

    model_config = {"from_attributes": True}
