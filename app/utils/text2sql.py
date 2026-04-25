import os
import dashscope
from dashscope import Generation
from app.config import get_settings

settings = get_settings()

# 完整的数据库表结构定义，包含所有字段、约束、外键关系和中文语义
DB_SCHEMA = """
=== 数据库表结构（MySQL，utf8mb4） ===

所有表共有字段 is_del INT 默认0（0-存在，1-删除），查询时所有表必须加 is_del=0 排除已删除记录。

────────────────────────────────────────
1. users（用户表/员工表）
────────────────────────────────────────
| 字段       | 类型          | 必填 | 默认 | 说明                                  |
|------------|---------------|------|------|---------------------------------------|
| uid        | INT           | 是   | 自增 | 主键，用户ID                          |
| username   | VARCHAR(20)   | 是   | -    | 登录账号，唯一                        |
| pwd        | VARCHAR(32)   | 是   | -    | 密码(MD5)，禁止查询此字段             |
| name       | VARCHAR(20)   | 是   | -    | 真实姓名                              |
| gender     | INT           | 否   | 0    | 性别：0-男，1-女                      |
| email      | VARCHAR(100)  | 否   | NULL | 邮箱                                  |
| phone      | VARCHAR(11)   | 是   | -    | 手机号                                |
| role       | INT           | 否   | 1    | 角色：0-管理员，1-普通员工，2-经理，3-学生 |
| create_time| DATETIME      | 否   | 当前 | 创建时间                              |
| is_del     | INT           | 否   | 0    | 0-存在，1-删除                        |

────────────────────────────────────────
2. customers（顾客表）
────────────────────────────────────────
| 字段          | 类型          | 必填 | 默认 | 说明                                                       |
|---------------|---------------|------|------|------------------------------------------------------------|
| c_id          | INT           | 是   | 自增 | 主键，顾客ID                                               |
| c_name        | VARCHAR(20)   | 是   | -    | 姓名                                                       |
| c_age         | INT           | 否   | NULL | 年龄                                                       |
| c_gender      | INT           | 否   | 0    | 性别：0-男，1-女                                           |
| c_phone       | VARCHAR(11)   | 是   | -    | 手机号                                                     |
| c_email       | VARCHAR(100)  | 否   | NULL | 邮箱                                                       |
| c_degree      | VARCHAR(20)   | 否   | NULL | 学历                                                       |
| c_region      | VARCHAR(20)   | 否   | NULL | 籍贯                                                       |
| c_suit_project| INT           | 否   | 0    | 符合项目：0-所有项目都符合，1-所有项目都不符合，2-新加坡国际本硕升学计划，3-中德精英人才共建计划 |
| c_rank        | VARCHAR(1)    | 否   | 'C'  | 顾客等级：S-核心顾客，A-重要顾客，B-普通顾客，C-一般顾客，D-边缘顾客 |
| create_time   | DATETIME      | 否   | 当前 | 创建时间                                                   |
| update_time   | DATETIME      | 否   | 当前 | 更新时间                                                   |
| link_uid      | INT           | 否   | NULL | 外键→users.uid，负责跟进该顾客的员工ID                     |
| c_status      | INT           | 否   | 0    | 联系状态：0-未联系，1-已联系未回复，2-已联系无意向，3-已联系有意向，4-已入学 |
| c_analyze_info| TEXT          | 否   | NULL | 分析信息                                                   |
| is_del        | INT           | 否   | 0    | 0-存在，1-删除                                             |

外键：customers.link_uid → users.uid

────────────────────────────────────────
3. work_repo（工作日报表）
────────────────────────────────────────
| 字段       | 类型          | 必填 | 默认 | 说明                          |
|------------|---------------|------|------|-------------------------------|
| w_id       | INT           | 是   | 自增 | 主键，日报ID                  |
| w_date     | DATE          | 否   | -    | 日报日期                      |
| w_title    | VARCHAR(100)  | 是   | -    | 日报标题                      |
| u_id       | INT           | 是   | -    | 外键→users.uid，写日报的员工  |
| content    | TEXT          | 否   | NULL | 日报内容                      |
| create_time| DATETIME      | 否   | 当前 | 创建时间                      |
| update_time| DATETIME      | 否   | 当前 | 更新时间                      |
| is_del     | INT           | 否   | 0    | 0-存在，1-删除                |

外键：work_repo.u_id → users.uid

────────────────────────────────────────
4. work_repo_sum（工作日报总结表）
────────────────────────────────────────
| 字段       | 类型          | 必填 | 默认 | 说明                          |
|------------|---------------|------|------|-------------------------------|
| ws_id      | INT           | 是   | 自增 | 主键，总结ID                  |
| ws_date    | DATE          | 是   | -    | 总结日期                      |
| ws_title   | VARCHAR(100)  | 是   | -    | 总结标题                      |
| content    | TEXT          | 否   | NULL | 总结内容                      |
| create_time| DATETIME      | 否   | 当前 | 创建时间                      |
| is_del     | INT           | 否   | 0    | 0-存在，1-删除                |

────────────────────────────────────────
5. industry_repo（行业周报表）
────────────────────────────────────────
| 字段       | 类型          | 必填 | 默认 | 说明                          |
|------------|---------------|------|------|-------------------------------|
| i_id       | INT           | 是   | 自增 | 主键，周报ID                  |
| i_title    | VARCHAR(100)  | 是   | -    | 周报标题                      |
| content    | TEXT          | 否   | NULL | 周报内容                      |
| create_time| DATETIME      | 否   | 当前 | 创建时间                      |
| is_del     | INT           | 否   | 0    | 0-存在，1-删除                |

=== 表关系（外键依赖） ===
1. customers.link_uid → users.uid
   含义：每个顾客由一个员工负责跟进，通过 link_uid 关联到 users 表
   JOIN示例：SELECT c.c_name, u.name AS 跟进员工 FROM customers c LEFT JOIN users u ON c.link_uid = u.uid WHERE c.is_del=0

2. work_repo.u_id → users.uid
   含义：每条工作日报由一个员工编写，通过 u_id 关联到 users 表
   JOIN示例：SELECT w.w_title, u.name AS 员工姓名 FROM work_repo w LEFT JOIN users u ON w.u_id = u.uid WHERE w.is_del=0

3. customers 和 work_repo 通过 users 表间接关联
   含义：可以通过 users 表关联查询某员工负责的顾客和该员工的日报
   JOIN示例：SELECT u.name, c.c_name AS 顾客, w.w_title AS 日报 FROM users u LEFT JOIN customers c ON u.uid=c.link_uid AND c.is_del=0 LEFT JOIN work_repo w ON u.uid=w.u_id AND w.is_del=0 WHERE u.is_del=0

=== 常用查询场景 ===
- 查某员工的顾客：WHERE c.link_uid = (员工uid)
- 查某员工的日报：WHERE w.u_id = (员工uid)
- 按员工名查顾客：JOIN users ON customers.link_uid = users.uid WHERE users.name LIKE '%姓名%'
- 按员工名查日报：JOIN users ON work_repo.u_id = users.uid WHERE users.name LIKE '%姓名%'
- 查某状态顾客：WHERE c_status = 0/1/2/3/4
- 查某等级顾客：WHERE c_rank = 'S'/'A'/'B'/'C'/'D'
- 按日期范围查日报：WHERE w_date BETWEEN '2024-01-01' AND '2024-12-31'
"""


def text2sql(question: str) -> dict:
    # 确保 dashscope 不走代理
    for key in ('HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy'):
        os.environ.pop(key, None)
    os.environ['NO_PROXY'] = '*'
    os.environ['no_proxy'] = '*'

    dashscope.api_key = settings.DASHSCOPE_API_KEY

    prompt = f"""你是一个专业的SQL转换专家。根据以下完整的数据库表结构定义，将用户的中文自然语言问题精准转换为MySQL SELECT查询语句。

{DB_SCHEMA}

=== 严格规则 ===
1. 【安全】只能生成SELECT查询语句，绝对禁止INSERT/UPDATE/DELETE/DROP/ALTER/CREATE/TRUNCATE等修改操作
2. 【安全】禁止查询pwd字段
3. 【必选】所有查询的每个表都必须加 is_del=0 条件（JOIN时每个表都要加）
4. 【限制】查询结果默认加 LIMIT 100
5. 【格式】只返回一条纯SQL语句，不要任何解释、注释或markdown代码块标记
6. 【模糊】涉及中文名称/标题查询时使用 LIKE '%关键词%' 模糊匹配
7. 【类型】c_rank 是 VARCHAR(1)，值为 'S'/'A'/'B'/'C'/'D'，查询时必须用引号如 c_rank='A'
8. 【JOIN】当查询涉及多个表的信息时，必须使用JOIN并通过外键关联
9. 【别名】多表查询时必须使用表别名（如 u/c/w），并在SELECT中用别名.字段避免歧义
10. 【错误】无法生成SQL时返回 "ERROR: 无法生成SQL"，用户要求非查询操作返回 "ERROR: 仅支持查询操作"

=== 术语映射 ===
- "顾客/客户" → customers表
- "用户/员工/成员" → users表
- "日报/工作日报" → work_repo表
- "日报总结/工作日报总结" → work_repo_sum表
- "周报/行业周报" → industry_repo表
- "跟进人/负责人" → customers.link_uid 关联 users
- "写日报的人" → work_repo.u_id 关联 users

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
            # 去除SQL中的注释行
            lines = [l for l in sql.split('\n') if not l.strip().startswith('--')]
            sql = '\n'.join(lines).strip()
            return {"sql": sql, "error": None}
        else:
            return {"sql": None, "error": f"API调用失败: {response.message}"}
    except Exception as e:
        return {"sql": None, "error": str(e)}
