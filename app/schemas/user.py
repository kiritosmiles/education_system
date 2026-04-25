from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
import re


class UserLogin(BaseModel):
    username: str = Field(..., min_length=5, max_length=20)
    pwd: str = Field(..., min_length=6, max_length=20)


class UserCreate(BaseModel):
    username: str = Field(..., min_length=5, max_length=20)
    pwd: str = Field(..., min_length=6, max_length=20)
    name: str = Field(..., min_length=2, max_length=20)
    gender: int = Field(0, ge=0, le=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: int = Field(1, ge=0, le=3)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r'^\d{11}$', v):
            raise ValueError("手机号必须为11位数字")
        return v


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=20)
    gender: Optional[int] = Field(None, ge=0, le=1)
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[int] = Field(None, ge=0, le=3)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v):
        if v:
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(pattern, v):
                raise ValueError("邮箱格式不正确")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v):
        if v and not re.match(r'^\d{11}$', v):
            raise ValueError("手机号必须为11位数字")
        return v


class UserPwdUpdate(BaseModel):
    old_pwd: str = Field(..., min_length=6, max_length=20)
    new_pwd: str = Field(..., min_length=6, max_length=20)


class UserOut(BaseModel):
    uid: int
    username: str
    name: str
    gender: int
    email: Optional[str] = None
    phone: Optional[str] = None
    role: int
    create_time: datetime
    is_del: int

    model_config = {"from_attributes": True}


class TokenData(BaseModel):
    uid: int
    role: int
