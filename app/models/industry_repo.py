from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from app.database import Base


class IndustryRepo(Base):
    __tablename__ = "industry_repo"

    i_id = Column(Integer, primary_key=True, autoincrement=True)
    i_title = Column(String(100), nullable=False)
    content = Column(Text, nullable=True)
    create_time = Column(DateTime, default=datetime.now)
    is_del = Column(Integer, default=0, comment="0-存在,1-删除")
