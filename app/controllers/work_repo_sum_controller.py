import logging
from datetime import date, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.work_repo import WorkRepo
from app.models.work_repo_sum import WorkRepoSum
from app.schemas.work_repo_sum import WorkRepoSumCreate, WorkRepoSumUpdate, WorkRepoSumOut
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user
from app.utils.dify_client import chat_message, extract_chat_answer
import asyncio

router = APIRouter(prefix="/api/work-repo-sums", tags=["工作日报总结"])
logger = logging.getLogger(__name__)


def check_admin_or_manager(current_user: User):
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅管理员和经理可访问工作日报总结")


@router.get("")
def list_work_repo_sums(
    ws_date: Optional[date] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_admin_or_manager(current_user)
    query = db.query(WorkRepoSum).filter(WorkRepoSum.is_del == 0)
    if ws_date:
        query = query.filter(WorkRepoSum.ws_date == ws_date)
    if start_date:
        query = query.filter(WorkRepoSum.ws_date >= start_date)
    if end_date:
        query = query.filter(WorkRepoSum.ws_date <= end_date)
    total = query.count()
    items = query.order_by(WorkRepoSum.ws_date.desc()).offset((page - 1) * size).limit(size).all()
    return ResponseBase(data={"total": total, "items": [WorkRepoSumOut.model_validate(s).model_dump() for s in items]})


@router.get("/{ws_id}")
def get_work_repo_sum(ws_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin_or_manager(current_user)
    s = db.query(WorkRepoSum).filter(WorkRepoSum.ws_id == ws_id, WorkRepoSum.is_del == 0).first()
    if not s:
        raise HTTPException(status_code=404, detail="工作日报总结不存在")
    return ResponseBase(data=WorkRepoSumOut.model_validate(s).model_dump())


@router.post("/generate")
async def generate_work_repo_sum(
    request: Request,
    ws_date: date = Query(..., description="生成指定日期的工作日报总结"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """手动生成指定日期的工作日报总结"""
    check_admin_or_manager(current_user)

    # 获取该日期所有员工工作日报
    repos = db.query(WorkRepo).filter(WorkRepo.is_del == 0, WorkRepo.w_date == ws_date).all()
    if not repos:
        raise HTTPException(status_code=400, detail=f"{ws_date} 没有员工工作日报数据")

    # 从请求头提取token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    # 拼接工作日报内容
    repos_text = f"日期：{ws_date}\n\n"
    for r in repos:
        repos_text += f"员工UID：{r.u_id}，标题：{r.w_title}\n内容：{r.content or '无'}\n\n"

    # 调用Dify Chatbot API生成总结
    try:
        result = await chat_message(
            query=f"生成{ws_date}的员工总结报告",
            user=f"uid_{current_user.uid}",
            inputs={"yesterday": str(ws_date)},
            uid=str(current_user.uid),
            token=token
        )
        content = extract_chat_answer(result)
    except Exception as e:
        logger.error(f"调用Dify API失败: {e}")
        raise HTTPException(status_code=500, detail=f"调用Dify API失败: {str(e)}")

    # 保存总结
    ws_title = f"{ws_date} 员工工作日报总结"
    summary = WorkRepoSum(ws_date=ws_date, ws_title=ws_title, content=content)
    db.add(summary)
    db.commit()
    db.refresh(summary)
    return ResponseBase(data=WorkRepoSumOut.model_validate(summary).model_dump(), msg="生成成功")


@router.delete("/{ws_id}")
def delete_work_repo_sum(ws_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    check_admin_or_manager(current_user)
    s = db.query(WorkRepoSum).filter(WorkRepoSum.ws_id == ws_id, WorkRepoSum.is_del == 0).first()
    if not s:
        raise HTTPException(status_code=404, detail="工作日报总结不存在")
    s.is_del = 1
    db.commit()
    return ResponseBase(msg="删除成功")


async def scheduled_generate_work_repo_sum():
    """定时任务：生成昨日工作日报总结"""
    from app.database import SessionLocal
    db = SessionLocal()
    try:
        yesterday = date.today() - timedelta(days=1)

        # 获取昨日工作日报
        repos = db.query(WorkRepo).filter(WorkRepo.is_del == 0, WorkRepo.w_date == yesterday).all()
        if not repos:
            logger.info(f"{yesterday} 没有员工工作日报数据，跳过生成")
            return

        # 拼接内容
        repos_text = f"日期：{yesterday}\n\n"
        for r in repos:
            repos_text += f"员工UID：{r.u_id}，标题：{r.w_title}\n内容：{r.content or '无'}\n\n"

        # 调用Dify Chatbot API
        result = await chat_message(
            query=f"生成{yesterday}的员工总结报告",
            user="system_scheduled",
            inputs={"yesterday": str(yesterday)}
        )
        content = extract_chat_answer(result)

        # 保存
        ws_title = f"{yesterday} 员工工作日报总结"
        summary = WorkRepoSum(ws_date=yesterday, ws_title=ws_title, content=content)
        db.add(summary)
        db.commit()
        logger.info(f"{yesterday} 工作日报总结生成成功")
    except Exception as e:
        logger.error(f"定时生成工作日报总结失败: {e}")
    finally:
        db.close()
