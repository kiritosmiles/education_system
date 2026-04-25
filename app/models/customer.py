from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    c_id = Column(Integer, primary_key=True, autoincrement=True)
    c_name = Column(String(20), nullable=False)
    c_age = Column(Integer, nullable=True)
    c_gender = Column(Integer, default=0, comment="0-男,1-女")
    c_phone = Column(String(11), nullable=True)
    c_email = Column(String(100), nullable=True)
    c_degree = Column(String(20), nullable=True)
    c_region = Column(String(20), nullable=True, comment="籍贯")
    c_suit_project = Column(Integer, default=0, comment="0-所有项目都符合,1-所有项目都不符合,2-新加坡国际本硕升学计划,3-中德精英人才共建计划")
    c_rank = Column(Integer, default=3, comment="0-核心顾客,1-重要顾客,2-普通顾客,3-边缘顾客")
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    link_uid = Column(Integer, ForeignKey("users.uid"), nullable=True)
    c_status = Column(Integer, default=0, comment="0-未联系,1-已联系未回复,2-已联系无意向,3-已联系有意向,4-已入学")
    c_analyze_info = Column(Text, nullable=True)
    is_del = Column(Integer, default=0, comment="0-存在,1-删除")

    link_user = relationship("User", back_populates="customers", foreign_keys=[link_uid])
