import logging
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.industry_repo import IndustryRepo
from app.schemas.industry_repo import IndustryRepoCreate, IndustryRepoUpdate, IndustryRepoOut
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user, require_role
from app.utils.dify_client import chat_message, extract_chat_answer
from app.config import get_settings

router = APIRouter(prefix="/api/industry-repos", tags=["行业周报"])
logger = logging.getLogger(__name__)
settings = get_settings()


def check_admin_or_manager(current_user: User):
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅管理员和经理可访问此功能")


@router.get("")
def list_industry_repos(
    i_title: Optional[str] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(IndustryRepo).filter(IndustryRepo.is_del == 0)
    if i_title:
        query = query.filter(IndustryRepo.i_title.like(f"%{i_title}%"))
    total = query.count()
    items = query.order_by(IndustryRepo.create_time.desc()).offset((page - 1) * size).limit(size).all()
    return ResponseBase(data={"total": total, "items": [IndustryRepoOut.model_validate(i).model_dump() for i in items]})


@router.get("/{i_id}")
def get_industry_repo(i_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    repo = db.query(IndustryRepo).filter(IndustryRepo.i_id == i_id, IndustryRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="行业周报不存在")
    return ResponseBase(data=IndustryRepoOut.model_validate(repo).model_dump())


@router.post("/generate")
async def generate_industry_repo(
    request: Request,
    start_date: date = Query(..., description="周报开始日期"),
    end_date: date = Query(..., description="周报结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动生成指定日期范围的行业周报"""
    check_admin_or_manager(current_user)

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="开始日期不能晚于结束日期")

    # 从请求头提取token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    # 调用Dify Chatbot API生成行业周报
    try:
        result = await chat_message(
            query=f"生成{start_date}~{end_date}的行业周报",
            user=f"uid_{current_user.uid}",
            inputs={"start_date": str(start_date), "end_date": str(end_date)},
            uid=str(current_user.uid),
            token=token,
            api_key=settings.DIFY_INDUSTRY_REPO_API_KEY
        )
        content = extract_chat_answer(result)
    except Exception as e:
        logger.error(f"调用Dify API生成行业周报失败: {e}")
        raise HTTPException(status_code=500, detail=f"调用Dify API失败: {str(e)}")

    # 保存周报
    i_title = f"{start_date}~{end_date} 行业周报"
    repo = IndustryRepo(i_title=i_title, content=content)
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return ResponseBase(data=IndustryRepoOut.model_validate(repo).model_dump(), msg="生成成功")


@router.post("")
def create_industry_repo(data: IndustryRepoCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(0, 1))):
    repo = IndustryRepo(
        i_title=data.i_title,
        content=data.content
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return ResponseBase(data=IndustryRepoOut.model_validate(repo).model_dump())


@router.put("/{i_id}")
def update_industry_repo(i_id: int, data: IndustryRepoUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_role(0, 1))):
    repo = db.query(IndustryRepo).filter(IndustryRepo.i_id == i_id, IndustryRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="行业周报不存在")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(repo, k, v)
    db.commit()
    db.refresh(repo)
    return ResponseBase(data=IndustryRepoOut.model_validate(repo).model_dump())


@router.delete("/{i_id}")
def delete_industry_repo(i_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_role(0, 1))):
    repo = db.query(IndustryRepo).filter(IndustryRepo.i_id == i_id, IndustryRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="行业周报不存在")
    repo.is_del = 1
    db.commit()
    return ResponseBase(msg="删除成功")


async def scheduled_generate_industry_repo():
    """定时任务：生成上周行业周报"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        today = date.today()
        # 计算上周一和上周日
        days_since_monday = today.weekday()  # Monday=0, Sunday=6
        last_monday = today - timedelta(days=days_since_monday + 7)
        last_sunday = last_monday + timedelta(days=6)

        # 调用Dify Chatbot API
        result = await chat_message(
            query=f"生成{last_monday}~{last_sunday}的行业周报",
            user="system_scheduled",
            inputs={"start_date": str(last_monday), "end_date": str(last_sunday)},
            api_key=settings.DIFY_INDUSTRY_REPO_API_KEY
        )
        content = extract_chat_answer(result)

        # 保存
        i_title = f"{last_monday}~{last_sunday} 行业周报"
        repo = IndustryRepo(i_title=i_title, content=content)
        db.add(repo)
        db.commit()
        logger.info(f"{last_monday}~{last_sunday} 行业周报生成成功")
    except Exception as e:
        logger.error(f"定时生成行业周报失败: {e}")
    finally:
        db.close()
