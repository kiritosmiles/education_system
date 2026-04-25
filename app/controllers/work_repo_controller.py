from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.work_repo import WorkRepo
from app.schemas.work_repo import WorkRepoCreate, WorkRepoUpdate, WorkRepoOut
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/work-repos", tags=["工作日报"])


@router.get("")
def list_work_repos(
    w_title: Optional[str] = None,
    u_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(WorkRepo).filter(WorkRepo.is_del == 0)
    # admin: 查看所有; manager: 查看所有; normal: 只看自己的; student: 无权限
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权查看工作日报")
    if current_user.role == 1:
        query = query.filter(WorkRepo.u_id == current_user.uid)
    # role=0 admin, role=2 manager: 可查看所有
    if w_title:
        query = query.filter(WorkRepo.w_title.like(f"%{w_title}%"))
    if u_id is not None:
        query = query.filter(WorkRepo.u_id == u_id)
    if start_date:
        query = query.filter(WorkRepo.w_date >= start_date)
    if end_date:
        query = query.filter(WorkRepo.w_date <= end_date)
    total = query.count()
    items = query.order_by(WorkRepo.w_date.desc()).offset((page - 1) * size).limit(size).all()
    return ResponseBase(data={"total": total, "items": [WorkRepoOut.model_validate(w).model_dump() for w in items]})


@router.get("/all/list")
def list_all_work_repos(
    w_date: date = Query(..., description="指定日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role not in (0, 2):
        raise HTTPException(status_code=403, detail="仅管理员和经理可查看所有员工日报")
    items = db.query(WorkRepo).filter(WorkRepo.is_del == 0, WorkRepo.w_date == w_date).order_by(WorkRepo.w_date.desc()).all()
    return ResponseBase(data=[WorkRepoOut.model_validate(w).model_dump() for w in items])


@router.get("/{w_id}")
def get_work_repo(w_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权查看工作日报")
    repo = db.query(WorkRepo).filter(WorkRepo.w_id == w_id, WorkRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="工作日报不存在")
    if current_user.role == 1 and repo.u_id != current_user.uid:
        raise HTTPException(status_code=403, detail="权限不足")
    return ResponseBase(data=WorkRepoOut.model_validate(repo).model_dump())


@router.post("")
def create_work_repo(data: WorkRepoCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权创建工作日报")
    repo = WorkRepo(
        w_date=data.w_date,
        w_title=data.w_title,
        u_id=current_user.uid,
        content=data.content
    )
    db.add(repo)
    db.commit()
    db.refresh(repo)
    return ResponseBase(data=WorkRepoOut.model_validate(repo).model_dump())


@router.put("/{w_id}")
def update_work_repo(w_id: int, data: WorkRepoUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权修改工作日报")
    repo = db.query(WorkRepo).filter(WorkRepo.w_id == w_id, WorkRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="工作日报不存在")
    # normal只能修改自己的, manager也只能修改自己的
    if current_user.role in (1, 2) and repo.u_id != current_user.uid:
        raise HTTPException(status_code=403, detail="只能修改自己的工作日报")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(repo, k, v)
    db.commit()
    db.refresh(repo)
    return ResponseBase(data=WorkRepoOut.model_validate(repo).model_dump())


@router.delete("/{w_id}")
def delete_work_repo(w_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权删除工作日报")
    repo = db.query(WorkRepo).filter(WorkRepo.w_id == w_id, WorkRepo.is_del == 0).first()
    if not repo:
        raise HTTPException(status_code=404, detail="工作日报不存在")
    if current_user.role in (1, 2) and repo.u_id != current_user.uid:
        raise HTTPException(status_code=403, detail="只能删除自己的工作日报")
    repo.is_del = 1
    db.commit()
    return ResponseBase(msg="删除成功")
