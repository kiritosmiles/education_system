from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Date, Text
from app.database import Base


class WorkRepoSum(Base):
    __tablename__ = "work_repo_sum"

    ws_id = Column(Integer, primary_key=True, autoincrement=True)
    ws_date = Column(Date, nullable=False, comment="工作日报总结日期")
    ws_title = Column(String(40), nullable=False, comment="工作日报总结标题")
    content = Column(Text, nullable=True, comment="内容")
    create_time = Column(DateTime, default=datetime.now)
    is_del = Column(Integer, default=0, comment="0-存在,1-删除")
