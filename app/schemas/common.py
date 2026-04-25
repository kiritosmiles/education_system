from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ResponseBase(BaseModel):
    code: int = 200
    msg: str = "success"
    data: Optional[dict | list] = None


class Text2SQLRequest(BaseModel):
    question: str


class EmailSendRequest(BaseModel):
    to_email: EmailStr
    subject: str
    content: str
    attachment_type: Optional[str] = None  # "work_repo" or "industry_repo"
    attachment_id: Optional[int] = None
