from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.customer import Customer
from app.schemas.customer import CustomerCreate, CustomerUpdate, CustomerOut
from app.schemas.common import ResponseBase
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/customers", tags=["顾客管理"])


@router.get("")
def list_customers(
    c_name: Optional[str] = None,
    c_phone: Optional[str] = None,
    c_status: Optional[int] = None,
    c_suit_project: Optional[int] = None,
    c_rank: Optional[str] = None,
    link_uid: Optional[int] = None,
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(Customer).filter(Customer.is_del == 0)
    # role=3 student: 只能看自己关联的顾客
    if current_user.role == 3:
        query = query.filter(Customer.link_uid == current_user.uid)
    # role=1 normal / role=2 manager: 可以CRUD所有顾客
    # role=0 admin: 可以查看所有
    if c_name:
        query = query.filter(Customer.c_name.like(f"%{c_name}%"))
    if c_phone:
        query = query.filter(Customer.c_phone.like(f"%{c_phone}%"))
    if c_status is not None:
        query = query.filter(Customer.c_status == c_status)
    if c_suit_project is not None:
        query = query.filter(Customer.c_suit_project == c_suit_project)
    if c_rank is not None:
        query = query.filter(Customer.c_rank == c_rank)
    if link_uid is not None:
        query = query.filter(Customer.link_uid == link_uid)
    total = query.count()
    items = query.offset((page - 1) * size).limit(size).all()
    return ResponseBase(data={"total": total, "items": [CustomerOut.model_validate(c).model_dump() for c in items]})


@router.get("/{c_id}")
def get_customer(c_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    customer = db.query(Customer).filter(Customer.c_id == c_id, Customer.is_del == 0).first()
    if not customer:
        raise HTTPException(status_code=404, detail="顾客不存在")
    if current_user.role == 3 and customer.link_uid != current_user.uid:
        raise HTTPException(status_code=403, detail="权限不足")
    return ResponseBase(data=CustomerOut.model_validate(customer).model_dump())


@router.post("")
def create_customer(data: CustomerCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权创建顾客")
    customer = Customer(
        c_name=data.c_name,
        c_age=data.c_age,
        c_gender=data.c_gender,
        c_phone=data.c_phone,
        c_email=data.c_email,
        c_degree=data.c_degree,
        c_region=data.c_region,
        c_suit_project=data.c_suit_project,
        c_rank=data.c_rank,
        link_uid=data.link_uid,
        c_status=data.c_status,
        c_analyze_info=data.c_analyze_info
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return ResponseBase(data=CustomerOut.model_validate(customer).model_dump())


@router.put("/{c_id}")
def update_customer(c_id: int, data: CustomerUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权修改顾客")
    customer = db.query(Customer).filter(Customer.c_id == c_id, Customer.is_del == 0).first()
    if not customer:
        raise HTTPException(status_code=404, detail="顾客不存在")
    update_data = data.model_dump(exclude_unset=True)
    for k, v in update_data.items():
        setattr(customer, k, v)
    db.commit()
    db.refresh(customer)
    return ResponseBase(data=CustomerOut.model_validate(customer).model_dump())


@router.delete("/{c_id}")
def delete_customer(c_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if current_user.role == 3:
        raise HTTPException(status_code=403, detail="学生无权删除顾客")
    customer = db.query(Customer).filter(Customer.c_id == c_id, Customer.is_del == 0).first()
    if not customer:
        raise HTTPException(status_code=404, detail="顾客不存在")
    customer.is_del = 1
    db.commit()
    return ResponseBase(msg="删除成功")
