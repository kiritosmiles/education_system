from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.industry_repo import IndustryRepo
from app.schemas.industry_repo import IndustryRepoCreate, IndustryRepoUpdate, IndustryRepoOut
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user, require_role

router = APIRouter(prefix="/api/industry-repos", tags=["行业周报"])


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
