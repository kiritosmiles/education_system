import re
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.user import User
from app.schemas.common import Text2SQLRequest, ResponseBase
from app.utils.auth import get_current_user
from app.utils.text2sql import text2sql

router = APIRouter(prefix="/api/text2sql", tags=["Text2SQL"])

# 表名 -> 中文
TABLE_LABELS = {
    "users": "用户表",
    "customers": "顾客表",
    "work_repo": "工作日报表",
    "work_repo_sum": "工作日报总结表",
    "industry_repo": "行业周报表",
}

# 字段英文 -> 中文映射（按表分组，支持同名字段区分）
COLUMN_LABELS = {
    # users
    "uid": "用户ID", "username": "用户名", "name": "姓名",
    "gender": "性别", "email": "邮箱", "phone": "手机号", "role": "角色",
    "create_time": "创建时间",
    # customers
    "c_id": "顾客ID", "c_name": "姓名", "c_age": "年龄", "c_gender": "性别",
    "c_phone": "手机号", "c_email": "邮箱", "c_degree": "学历",
    "c_region": "籍贯", "c_suit_project": "符合项目", "c_rank": "顾客等级",
    "update_time": "更新时间", "link_uid": "跟进员工ID",
    "c_status": "联系状态", "c_analyze_info": "分析信息",
    # work_repo
    "w_id": "日报ID", "w_date": "日报日期", "w_title": "日报标题",
    "u_id": "员工ID", "content": "内容",
    # work_repo_sum
    "ws_id": "总结ID", "ws_date": "总结日期", "ws_title": "总结标题",
    # industry_repo
    "i_id": "周报ID", "i_title": "周报标题",
}

# JOIN场景下同名字段按表区分的中文映射
# 格式: "表别名.字段" -> "中文标签"
JOIN_COLUMN_LABELS = {
    # users 别名 u
    "u.uid": "用户ID", "u.username": "用户名", "u.name": "员工姓名",
    "u.gender": "性别", "u.email": "邮箱", "u.phone": "手机号", "u.role": "角色",
    "u.create_time": "创建时间",
    # users 别名 users
    "users.uid": "用户ID", "users.username": "用户名", "users.name": "员工姓名",
    "users.gender": "性别", "users.email": "邮箱", "users.phone": "手机号", "users.role": "角色",
    "users.create_time": "创建时间",
    # customers 别名 c
    "c.c_id": "顾客ID", "c.c_name": "顾客姓名", "c.c_age": "年龄", "c.c_gender": "性别",
    "c.c_phone": "手机号", "c.c_email": "邮箱", "c.c_degree": "学历",
    "c.c_region": "籍贯", "c.c_suit_project": "符合项目", "c.c_rank": "顾客等级",
    "c.link_uid": "跟进员工ID", "c.c_status": "联系状态", "c.c_analyze_info": "分析信息",
    # customers 别名 customers
    "customers.c_id": "顾客ID", "customers.c_name": "顾客姓名",
    # work_repo 别名 w
    "w.w_id": "日报ID", "w.w_date": "日报日期", "w.w_title": "日报标题",
    "w.u_id": "员工ID", "w.content": "日报内容",
    # work_repo 别名 work_repo
    "work_repo.w_id": "日报ID", "work_repo.w_title": "日报标题",
    # work_repo_sum 别名 ws
    "ws.ws_id": "总结ID", "ws.ws_date": "总结日期", "ws.ws_title": "总结标题",
    "ws.content": "总结内容",
    # industry_repo 别名 i
    "i.i_id": "周报ID", "i.i_title": "周报标题", "i.content": "周报内容",
}

# 敏感字段，不返回给前端
HIDDEN_COLUMNS = {"pwd", "is_del"}

# 字段值 -> 中文映射
VALUE_LABELS = {
    "gender": {0: "男", 1: "女"},
    "c_gender": {0: "男", 1: "女"},
    "role": {0: "管理员", 1: "普通员工", 2: "经理", 3: "学生"},
    "c_status": {0: "未联系", 1: "已联系未回复", 2: "已联系无意向", 3: "已联系有意向", 4: "已入学"},
    "c_suit_project": {0: "所有项目都符合", 1: "所有项目都不符合", 2: "新加坡国际本硕升学计划", 3: "中德精英人才共建计划"},
    "c_rank": {"S": "核心顾客", "A": "重要顾客", "B": "普通顾客", "C": "一般顾客", "D": "边缘顾客"},
}


def _resolve_column_label(col_name: str) -> str:
    """根据列名生成中文标签，优先使用JOIN映射"""
    if col_name in JOIN_COLUMN_LABELS:
        return JOIN_COLUMN_LABELS[col_name]
    if col_name in COLUMN_LABELS:
        return COLUMN_LABELS[col_name]
    # 处理 表别名.字段 格式
    if '.' in col_name:
        parts = col_name.split('.', 1)
        alias, field = parts[0], parts[1]
        if field in COLUMN_LABELS:
            return f"{COLUMN_LABELS[field]}({alias})"
    return col_name


@router.post("/query")
def query_by_natural_language(
    data: Text2SQLRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = text2sql(data.question)
    if result["error"]:
        raise HTTPException(status_code=500, detail=result["error"])

    sql = result["sql"]
    if sql.startswith("ERROR"):
        raise HTTPException(status_code=400, detail=sql.replace("ERROR: ", ""))

    # 安全检查：只允许SELECT语句
    sql_stripped = sql.strip()
    # 去除开头的注释
    while sql_stripped.startswith("--") or sql_stripped.startswith("/*"):
        if sql_stripped.startswith("--"):
            sql_stripped = sql_stripped.split("\n", 1)[-1].strip()
        elif sql_stripped.startswith("/*"):
            end = sql_stripped.find("*/")
            if end == -1:
                raise HTTPException(status_code=400, detail="仅支持查询操作")
            sql_stripped = sql_stripped[end + 2:].strip()

    sql_upper = sql_stripped.upper()
    if not sql_upper.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="仅支持查询操作")

    # 检查是否包含危险关键字
    dangerous_patterns = [
        r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bREPLACE\b',
        r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b',
        r'\bINTO\s+OUTFILE\b', r'\bINTO\s+DUMPFILE\b',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            raise HTTPException(status_code=400, detail="仅支持查询操作")

    # 如果没有LIMIT，自动加上
    if not re.search(r'\bLIMIT\s+\d+', sql_upper):
        sql = sql.rstrip(";") + " LIMIT 100"

    try:
        rows = db.execute(text(sql)).fetchall()
        columns = list(rows[0]._mapping.keys()) if rows else []
        # 过滤敏感字段
        safe_columns = [c for c in columns if c not in HIDDEN_COLUMNS]
        data_list = []
        for row in rows:
            row_dict = dict(row._mapping)
            safe_row = {}
            for c in safe_columns:
                val = row_dict.get(c)
                # 尝试匹配值映射（纯字段名，不带别名）
                field_name = c.split('.')[-1] if '.' in c else c
                mapping = VALUE_LABELS.get(field_name) or VALUE_LABELS.get(c)
                safe_row[c] = mapping.get(val, val) if mapping and val is not None else val
            data_list.append(safe_row)
        # 生成中文列标题
        labels = [_resolve_column_label(col) for col in safe_columns]
        return ResponseBase(data={
            "sql": sql,
            "columns": safe_columns,
            "labels": labels,
            "rows": data_list,
            "total": len(data_list)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL执行失败: {str(e)}")
