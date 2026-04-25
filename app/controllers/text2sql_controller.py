from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.models.user import User
from app.schemas.common import Text2SQLRequest, ResponseBase
from app.utils.auth import get_current_user
from app.utils.text2sql import text2sql

router = APIRouter(prefix="/api/text2sql", tags=["Text2SQL"])

# 字段英文 -> 中文映射
COLUMN_LABELS = {
    # users
    "uid": "用户ID", "username": "用户名", "name": "姓名",
    "gender": "性别", "email": "邮箱", "phone": "手机号", "role": "角色",
    "create_time": "创建时间",
    # customers
    "c_id": "顾客ID", "c_name": "姓名", "c_age": "年龄", "c_gender": "性别",
    "c_phone": "手机号", "c_email": "邮箱", "c_degree": "学历",
    "c_region": "籍贯", "c_suit_project": "符合项目",
    "update_time": "更新时间", "link_uid": "关联用户ID",
    "c_status": "状态", "c_analyze_info": "分析信息",
    # work_repo
    "w_id": "日报ID", "w_date": "日期", "w_title": "标题",
    "u_id": "用户ID", "content": "内容",
    # industry_repo
    "i_id": "周报ID", "i_title": "标题",
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
}


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
        raise HTTPException(status_code=400, detail=sql)

    # 安全检查：只允许SELECT语句
    sql_stripped = sql.strip()
    # 去除开头的注释
    while sql_stripped.startswith("--") or sql_stripped.startswith("/*"):
        if sql_stripped.startswith("--"):
            sql_stripped = sql_stripped.split("\n", 1)[-1].strip()
        elif sql_stripped.startswith("/*"):
            end = sql_stripped.find("*/")
            if end == -1:
                raise HTTPException(status_code=400, detail="仅支持查询操作(SELECT)")
            sql_stripped = sql_stripped[end + 2:].strip()

    sql_upper = sql_stripped.upper()
    if not sql_upper.startswith("SELECT"):
        raise HTTPException(status_code=400, detail="仅支持查询操作(SELECT)")

    # 检查是否包含危险关键字（整句检查，忽略大小写）
    import re
    dangerous_patterns = [
        r'\bINSERT\b', r'\bUPDATE\b', r'\bDELETE\b', r'\bDROP\b',
        r'\bALTER\b', r'\bCREATE\b', r'\bTRUNCATE\b', r'\bREPLACE\b',
        r'\bGRANT\b', r'\bREVOKE\b', r'\bEXEC\b', r'\bEXECUTE\b',
        r'\bINTO\s+OUTFILE\b', r'\bINTO\s+DUMPFILE\b',
    ]
    for pattern in dangerous_patterns:
        if re.search(pattern, sql_upper):
            raise HTTPException(status_code=400, detail="仅支持查询操作(SELECT)")

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
                mapping = VALUE_LABELS.get(c)
                safe_row[c] = mapping.get(val, val) if mapping and val is not None else val
            data_list.append(safe_row)
        # 生成中文列标题
        labels = [COLUMN_LABELS.get(col, col) for col in safe_columns]
        return ResponseBase(data={
            "sql": sql,
            "columns": safe_columns,
            "labels": labels,
            "rows": data_list,
            "total": len(data_list)
        })
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"SQL执行失败: {str(e)}")
