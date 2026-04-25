from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.database import Base


class WorkRepo(Base):
    __tablename__ = "work_repo"

    w_id = Column(Integer, primary_key=True, autoincrement=True)
    w_date = Column(Date, nullable=False)
    w_title = Column(String(100), nullable=False)
    u_id = Column(Integer, ForeignKey("users.uid"), nullable=False)
    content = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    update_time = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    is_del = Column(Integer, default=0, comment="0-存在,1-删除")

    author = relationship("User", back_populates="work_repos", foreign_keys=[u_id])
