# Education System

基于 FastAPI 的教育管理系统，采用 MVC 架构，符合 RESTful 规范和 Pydantic 规范，使用 SQLAlchemy 与 MySQL 数据库交互。

## 项目结构

```
education_system/
├── app/
│   ├── __init__.py
│   ├── main.py                # 应用入口
│   ├── config.py              # 配置管理（读取.env）
│   ├── database.py            # 数据库连接
│   ├── models/                # SQLAlchemy ORM 模型（按表拆分）
│   │   ├── __init__.py
│   │   ├── user.py            # 用户模型
│   │   ├── customer.py        # 顾客模型
│   │   ├── work_repo.py       # 工作日报模型
│   │   └── industry_repo.py   # 行业周报模型
│   ├── schemas/               # Pydantic 数据验证模型（按模块拆分）
│   │   ├── __init__.py
│   │   ├── user.py            # 用户请求/响应模型
│   │   ├── customer.py        # 顾客请求/响应模型
│   │   ├── work_repo.py       # 工作日报请求/响应模型
│   │   ├── industry_repo.py   # 行业周报请求/响应模型
│   │   └── common.py          # 通用响应体 & Text2SQL/邮件请求体
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py       # 登录认证
│   │   ├── user_controller.py       # 用户CRUD
│   │   ├── customer_controller.py   # 顾客CRUD
│   │   ├── work_repo_controller.py  # 工作日报CRUD
│   │   ├── industry_repo_controller.py # 行业周报CRUD
│   │   ├── email_controller.py      # 邮件推送
│   │   └── text2sql_controller.py   # Text2SQL智能查询
│   ├── middleware/            # 中间件
│   │   ├── __init__.py
│   │   ├── logging_mw.py     # 日志初始化（控制台彩色 + 文件轮转）
│   │   └── access_mw.py      # 请求访问日志中间件
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py           # JWT/MD5认证工具
│   │   ├── email_sender.py   # SMTP邮件发送
│   │   └── text2sql.py       # 阿里云DashScope Text2SQL
│   ├── templates/             # Jinja2前端模板
│   │   ├── base.html
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   ├── users.html
│   │   ├── customers.html
│   │   ├── work_repos.html
│   │   ├── industry_repos.html
│   │   ├── email.html
│   │   └── text2sql.html
│   └── static/                # 静态资源
│       ├── css/
│       └── js/
├── log/                       # 日志目录
│   ├── app.log               # 应用日志（自动轮转，保留7天）
│   └── app_error.log         # 错误日志（自动轮转，保留7天）
├── .env                      # 环境变量配置
├── requirements.txt          # Python依赖
├── migrate.py                # 数据库迁移脚本
├── test_mw.py                # 中间件测试
└── README.md
```

## 环境要求

- Python 3.10+
- MySQL 8.0+

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件，填写以下配置：

```env
# 数据库
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=education_system

# JWT
JWT_SECRET=your_jwt_secret_key_change_this
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# SMTP (163邮箱)
SMTP_HOST=smtp.163.com
SMTP_PORT=465
SMTP_USER=your_email@163.com
SMTP_PASSWORD=your_smtp_auth_code

# 阿里云DashScope (通义千问)
DASHSCOPE_API_KEY=your_dashscope_api_key

# 日志级别（可选，默认INFO）
LOG_LEVEL=INFO
```

### 3. 创建数据库

```sql
CREATE DATABASE education_system DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 4. 数据库迁移

```bash
python migrate.py
```

### 5. 启动服务

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6. 访问系统

浏览器打开 `http://localhost:8000`

默认管理员账号：`admin` / `admin123`

## API 接口

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 认证 | POST | `/api/auth/login` | 用户登录 |
| 认证 | GET | `/api/auth/info` | 获取当前用户信息 |
| 用户 | GET | `/api/users` | 用户列表（管理员） |
| 用户 | GET | `/api/users/{uid}` | 用户详情 |
| 用户 | POST | `/api/users` | 创建用户（管理员） |
| 用户 | PUT | `/api/users/{uid}` | 更新用户 |
| 用户 | PUT | `/api/users/{uid}/pwd` | 修改密码 |
| 用户 | DELETE | `/api/users/{uid}` | 删除用户（管理员） |
| 顾客 | GET | `/api/customers` | 顾客列表 |
| 顾客 | GET | `/api/customers/{c_id}` | 顾客详情 |
| 顾客 | POST | `/api/customers` | 创建顾客 |
| 顾客 | PUT | `/api/customers/{c_id}` | 更新顾客 |
| 顾客 | DELETE | `/api/customers/{c_id}` | 删除顾客 |
| 工作日报 | GET | `/api/work-repos` | 日报列表 |
| 工作日报 | GET | `/api/work-repos/{w_id}` | 日报详情 |
| 工作日报 | POST | `/api/work-repos` | 创建日报 |
| 工作日报 | PUT | `/api/work-repos/{w_id}` | 更新日报 |
| 工作日报 | DELETE | `/api/work-repos/{w_id}` | 删除日报 |
| 行业周报 | GET | `/api/industry-repos` | 周报列表 |
| 行业周报 | GET | `/api/industry-repos/{i_id}` | 周报详情 |
| 行业周报 | POST | `/api/industry-repos` | 创建周报 |
| 行业周报 | PUT | `/api/industry-repos/{i_id}` | 更新周报 |
| 行业周报 | DELETE | `/api/industry-repos/{i_id}` | 删除周报 |
| 邮件 | POST | `/api/email/send` | 发送邮件 |
| 智能查询 | POST | `/api/text2sql/query` | 自然语言转SQL查询 |

## 权限说明

| 角色 | role值 | 权限 |
|------|--------|------|
| 管理员 | 0 | 查看所有页面和所有信息 |
| 普通员工 | 1 | CRUD所有顾客、CRUD自己的工作日报、CRUD行业周报 |
| 经理 | 2 | CRUD所有顾客、查看所有工作日报、CRUD自己的工作日报 |
| 学生 | 3 | 查看与自己关联的顾客 |

## 数据库表

- **users**: 用户表（uid, username, pwd, name, gender, email, phone, role, create_time, is_del）
- **customers**: 顾客表（c_id, c_name, c_age, c_gender, c_phone, c_email, c_degree, c_region, c_suit_project, create_time, update_time, link_uid, c_status, c_info, c_analyze_info, is_del）
- **work_repo**: 工作日报表（w_id, w_date, w_title, u_id, content, create_time, update_time, is_del）
- **industry_repo**: 行业周报表（i_id, i_title, content, create_time, is_del）

## Text2SQL 智能查询

系统集成了基于阿里云 DashScope（通义千问）的 Text2SQL 功能，支持自然语言转 SQL 查询，具备以下特性：

- **中文字段映射**：查询结果表头自动转换为中文显示
- **值翻译**：性别、角色、状态等数字字段自动映射为中文（如 gender: 0→男, 1→女）
- **安全限制**：仅允许 SELECT 查询，自动拦截 INSERT/UPDATE/DELETE/DROP 等危险操作
- **敏感字段过滤**：自动隐藏 `pwd`、`is_del` 等敏感/内部字段
- **SQL注入防护**：过滤注释、拦截危险关键字和文件操作

## 日志系统

- **控制台输出**：带 ANSI 颜色的格式化日志
- **应用日志**：`log/app.log`，按天轮转，保留7天
- **错误日志**：`log/app_error.log`，仅记录 ERROR 级别，按天轮转，保留7天
- **访问日志**：中间件自动记录请求 IP、方法、路径、状态码、处理耗时
- **日志级别**：通过 `.env` 中 `LOG_LEVEL` 配置，默认 `INFO`

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Pydantic
- **认证**: JWT Token + MD5密码加密
- **邮件**: aiosmtplib + 163邮箱SMTP
- **AI**: 阿里云DashScope (通义千问) Text2SQL
- **日志**: Python logging + TimedRotatingFileHandler
- **前端**: Bootstrap 5 + Jinja2模板
- **数据库**: MySQL 8.0
