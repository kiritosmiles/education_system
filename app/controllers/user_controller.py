from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate, UserPwdUpdate, UserOut
from app.schemas.common import ResponseBase
from app.utils.auth import md5_hash, get_current_user, require_role

router = APIRouter(prefix="/api/users", tags=["用户管理"])


@router.get("", response_model=None)
def list_users(
    username: Optional[str] = None,
    name: Optional[str] = None,
    gender: Optional[int] = None,
    role: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != 0:
        raise HTTPException(status_code=403, detail="仅管理员可查看用户列表")
    query = db.query(User).filter(User.is_del == 0)
    if username:
        query = query.filter(User.username.like(f"%{username}%"))
    if name:
        query = query.filter(User.name.like(f"%{name}%"))
    if gender is not None:
        query = query.filter(User.gender == gender)
    if role is not None:
        query = query.filter(User.role == role)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return ResponseBase(data={"total": total, "items": [UserOut.model_validate(u).model_dump() for u in items]})


@router.get("/{uid}")
def get_user(uid: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != 0 and current_user.uid != uid:
        raise HTTPException(status_code=403, detail="权限不足")
    user = db.query(User).filter(User.uid == uid, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return ResponseBase(data=UserOut.model_validate(user).model_dump())


@router.post("")
def create_user(data: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_role(0))):
    exists = db.query(User).filter(User.username == data.username, User.is_del == 0).first()
    if exists:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = User(
        username=data.username,
        pwd=md5_hash(data.pwd),
        name=data.name,
        gender=data.gender,
        email=data.email,
        phone=data.phone,
        role=data.role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ResponseBase(data=UserOut.model_validate(user).model_dump())


@router.put("/{uid}")
def update_user(uid: int, data: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role != 0 and current_user.uid != uid:
        raise HTTPException(status_code=403, detail="权限不足")
    user = db.query(User).filter(User.uid == uid, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(user, k, v)
    db.commit()
    db.refresh(user)
    return ResponseBase(data=UserOut.model_validate(user).model_dump())


@router.put("/{uid}/pwd")
def update_pwd(uid: int, data: UserPwdUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.uid != uid and current_user.role != 0:
        raise HTTPException(status_code=403, detail="权限不足")
    user = db.query(User).filter(User.uid == uid, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    if user.pwd != md5_hash(data.old_pwd) and current_user.role != 0:
        raise HTTPException(status_code=400, detail="原密码错误")
    user.pwd = md5_hash(data.new_pwd)
    db.commit()
    return ResponseBase(msg="密码修改成功")


@router.delete("/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), current_user: User = Depends(require_role(0))):
    user = db.query(User).filter(User.uid == uid, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.is_del = 1
    db.commit()
    return ResponseBase(msg="删除成功")
