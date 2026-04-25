from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.work_repo import WorkRepo
from app.models.industry_repo import IndustryRepo
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user
from app.utils.email_sender import send_email

router = APIRouter(prefix="/api/email", tags=["邮件推送"])


@router.post("/send")
async def send_report_email(
    to_email: str = Form(...),
    subject: str = Form(...),
    content: str = Form(...),
    attachment_type: Optional[str] = Form(None),
    attachment_id: Optional[int] = Form(None),
    files: List[UploadFile] = File(default=[]),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    attachment_content = ""
    if attachment_type and attachment_id:
        if attachment_type == "work_repo":
            repo = db.query(WorkRepo).filter(WorkRepo.w_id == attachment_id, WorkRepo.is_del == 0).first()
            if repo:
                attachment_content = f"\n\n--- 附件：工作日报 ---\n标题：{repo.w_title}\n日期：{repo.w_date}\n内容：{repo.content}"
        elif attachment_type == "industry_repo":
            repo = db.query(IndustryRepo).filter(IndustryRepo.i_id == attachment_id, IndustryRepo.is_del == 0).first()
            if repo:
                attachment_content = f"\n\n--- 附件：行业周报 ---\n标题：{repo.i_title}\n内容：{repo.content}"

    full_content = content + attachment_content

    attachments = []
    for f in files:
        file_content = await f.read()
        if file_content:
            maintype, subtype = (f.content_type or "application/octet-stream").split("/", 1)
            attachments.append({
                "filename": f.filename,
                "content": file_content,
                "maintype": maintype,
                "subtype": subtype,
            })

    success = await send_email(to_email, subject, full_content, html=False, attachments=attachments if attachments else None)
    if not success:
        raise HTTPException(status_code=500, detail="邮件发送失败")
    return ResponseBase(msg="邮件发送成功")
