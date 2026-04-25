import dashscope
from dashscope import Generation
from app.config import get_settings

settings = get_settings()

DB_SCHEMA = """
数据库表结构如下：
1. users（用户表）: uid(主键自增int), username(varchar20), pwd(varchar32 md5), name(varchar20), gender(int 0男1女), email(varchar100), phone(varchar11), role(int 0-admin,1-normal,2-manager,3-student), create_time(datetime), is_del(int 0存在1删除)
2. customers（顾客表）: c_id(主键自增), c_name(varchar20), c_age(int), c_gender(int 0男1女), c_phone(varchar11), c_email(varchar100), c_degree(varchar20), c_region(varchar20 籍贯), c_suit_project(int 0-所有项目都符合,1-所有项目都不符合,2-新加坡国际本硕升学计划,3-中德精英人才共建计划), c_rank(int 0-核心顾客,1-重要顾客,2-普通顾客,3-边缘顾客), create_time(datetime), update_time(datetime), link_uid(int外键uid), c_status(int 0未联系1已联系未回复2已联系无意向3已联系有意向4已入学), c_analyze_info(text), is_del(int 0存在1删除)
3. work_repo（工作日报表）: w_id(主键自增), w_date(datetime), w_title(varchar20), u_id(int外键uid), content(text), create_time(datetime), update_time(datetime), is_del(int 0存在1删除)
4. industry_repo（行业周报表）: i_id(主键自增), i_title(varchar20), content(text), create_time(datetime), is_del(int 0存在1删除)
"""


def text2sql(question: str) -> dict:
    dashscope.api_key = settings.DASHSCOPE_API_KEY

    prompt = f"""你是一个SQL专家。根据以下数据库表结构，将用户的自然语言问题转换为MySQL SQL查询语句。

{DB_SCHEMA}

规则：
1. 查询时默认加上 is_del=0 的条件（排除已删除的记录）
2. 只允许生成SELECT查询语句，严禁生成INSERT、UPDATE、DELETE、DROP、ALTER、CREATE、TRUNCATE等任何修改数据的语句
3. 如果用户的问题涉及增删改操作，返回 "ERROR: 仅支持查询操作"
4. 只返回一条SQL语句，不要任何解释
5. 如果无法生成SQL，返回 "ERROR: 无法生成SQL"

用户问题：{question}

请生成SQL："""

    try:
        response = Generation.call(
            model="qwen-turbo",
            prompt=prompt,
            max_tokens=500,
            temperature=0.1,
        )

        if response.status_code == 200:
            sql = response.output.text.strip()
            sql = sql.replace("```sql", "").replace("```", "").strip()
            return {"sql": sql, "error": None}
        else:
            return {"sql": None, "error": f"API调用失败: {response.message}"}
    except Exception as e:
        return {"sql": None, "error": str(e)}
