from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class IndustryRepoCreate(BaseModel):
    i_title: str = Field(..., max_length=20)
    content: Optional[str] = None


class IndustryRepoUpdate(BaseModel):
    i_title: Optional[str] = Field(None, max_length=20)
    content: Optional[str] = None


class IndustryRepoOut(BaseModel):
    i_id: int
    i_title: str
    content: Optional[str] = None
    create_time: datetime
    is_del: int

    model_config = {"from_attributes": True}
