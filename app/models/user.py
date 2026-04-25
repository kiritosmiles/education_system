from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    uid = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(20), unique=True, nullable=False)
    pwd = Column(String(32), nullable=False)
    name = Column(String(20), nullable=False)
    gender = Column(Integer, default=0, comment="0-男,1-女")
    email = Column(String(100), nullable=True)
    phone = Column(String(11), nullable=False)
    role = Column(Integer, default=1, comment="0-admin,1-normal,2-manager,3-student")
    create_time = Column(DateTime, default=datetime.now)
    is_del = Column(Integer, default=0, comment="0-存在,1-删除")

    customers = relationship("Customer", back_populates="link_user", foreign_keys="Customer.link_uid")
    work_repos = relationship("WorkRepo", back_populates="author", foreign_keys="WorkRepo.u_id")
