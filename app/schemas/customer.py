from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator
import re

RANK_VALUES = ("S", "A", "B", "C", "D")


class CustomerCreate(BaseModel):
    c_name: str = Field(..., min_length=2, max_length=20)
    c_age: Optional[int] = Field(None, ge=0, le=150)
    c_gender: int = Field(0, ge=0, le=1)
    c_phone: str
    c_email: Optional[str] = None
    c_degree: Optional[str] = None
    c_region: Optional[str] = Field(None, min_length=1, max_length=20)
    c_suit_project: int = Field(0, ge=0, le=3)
    c_rank: str = Field("C", pattern="^[SABCD]$")
    link_uid: Optional[int] = None
    c_status: int = Field(0, ge=0, le=4)
    c_analyze_info: Optional[str] = None

    @field_validator("c_email", mode="before")
    @classmethod
    def validate_email(cls, v):
        if v:
            v = v.strip()
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("邮箱格式不正确")
        return v

    @field_validator("c_phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        if v:
            v = v.strip()
        if not re.match(r'^\d{11}$', v):
            raise ValueError("手机号必须为11位数字")
        return v


class CustomerUpdate(BaseModel):
    c_name: Optional[str] = Field(None, min_length=2, max_length=20)
    c_age: Optional[int] = Field(None, ge=0, le=150)
    c_gender: Optional[int] = Field(None, ge=0, le=1)
    c_phone: Optional[str] = Field(None, min_length=11, max_length=11)
    c_email: Optional[str] = None
    c_degree: Optional[str] = None
    c_region: Optional[str] = Field(None, min_length=1, max_length=20)
    c_suit_project: Optional[int] = Field(None, ge=0, le=3)
    c_rank: Optional[str] = Field(None, pattern="^[SABCD]$")
    link_uid: Optional[int] = None
    c_status: Optional[int] = Field(None, ge=0, le=4)
    c_analyze_info: Optional[str] = None

    @field_validator("c_email", mode="before")
    @classmethod
    def validate_email(cls, v):
        if v:
            v = v.strip()
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("邮箱格式不正确")
        return v

    @field_validator("c_phone", mode="before")
    @classmethod
    def validate_phone(cls, v):
        if v:
            v = v.strip()
            if not re.match(r'^\d{11}$', v):
                raise ValueError("手机号必须为11位数字")
        return v


class CustomerOut(BaseModel):
    c_id: int
    c_name: str
    c_age: Optional[int] = None
    c_gender: int
    c_phone: str
    c_email: Optional[str] = None
    c_degree: Optional[str] = None
    c_region: Optional[str] = None
    c_suit_project: int = 0
    c_rank: str = "C"
    create_time: datetime
    update_time: datetime
    link_uid: Optional[int] = None
    c_status: int
    c_analyze_info: Optional[str] = None
    is_del: int

    model_config = {"from_attributes": True}
