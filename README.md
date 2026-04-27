# Education System

基于 FastAPI 的教育管理系统，采用 MVC 架构，符合 RESTful 规范和 Pydantic 规范，使用 SQLAlchemy 与 MySQL 数据库交互。集成 Dify AI 实现工作日报总结和行业周报的智能生成。前端采用暗黑系风格主题设计，集成 Live2D 看板娘。

## 项目结构

```
education_system/
├── app/
│   ├── __init__.py
│   ├── main.py                # 应用入口、路由注册、生命周期管理（lifespan）、统一异常处理
│   ├── config.py              # 配置管理（读取.env）
│   ├── database.py            # 数据库连接
│   ├── models/                # SQLAlchemy ORM 模型（按表拆分）
│   │   ├── __init__.py
│   │   ├── user.py            # 用户模型
│   │   ├── customer.py        # 顾客模型（含评级/适配项目/分析信息）
│   │   ├── work_repo.py       # 工作日报模型
│   │   ├── industry_repo.py   # 行业周报模型
│   │   └── work_repo_sum.py   # 工作日报总结模型
│   ├── schemas/               # Pydantic 数据验证模型（按模块拆分）
│   │   ├── __init__.py
│   │   ├── user.py            # 用户请求/响应模型
│   │   ├── customer.py        # 顾客请求/响应模型
│   │   ├── work_repo.py       # 工作日报请求/响应模型
│   │   ├── industry_repo.py   # 行业周报请求/响应模型
│   │   ├── work_repo_sum.py   # 工作日报总结请求/响应模型
│   │   └── common.py          # 通用响应体 & Text2SQL/邮件请求体
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py             # 登录认证
│   │   ├── user_controller.py             # 用户CRUD
│   │   ├── customer_controller.py         # 顾客CRUD
│   │   ├── work_repo_controller.py        # 工作日报CRUD
│   │   ├── work_repo_sum_controller.py    # 工作日报总结（含AI生成+定时任务）
│   │   ├── industry_repo_controller.py    # 行业周报CRUD（含AI生成+定时任务）
│   │   ├── email_controller.py            # 邮件推送
│   │   ├── text2sql_controller.py         # Text2SQL智能查询
│   │   └── ai_chat_controller.py          # AI智能助手（Dify Chat API，支持文件上传，阻塞/流式双模式）
│   ├── middleware/            # 中间件
│   │   ├── __init__.py
│   │   ├── logging_mw.py     # 日志初始化（控制台彩色 + 文件轮转）
│   │   └── access_mw.py      # 请求访问日志中间件
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── auth.py           # JWT/MD5认证工具
│   │   ├── dify_client.py    # Dify API客户端（Chat阻塞/流式模式 + 文件上传 + 全局连接池复用 + 工作流输出提取）
│   │   ├── email_sender.py   # SMTP邮件发送
│   │   └── text2sql.py       # 阿里云DashScope Text2SQL
│   ├── templates/             # Jinja2前端模板
│   │   ├── base.html          # 基础布局（暗黑系风格主题、全局样式）
│   │   ├── home.html          # 首页（企业展示 + Live2D看板娘 + Dify嵌入式聊天）
│   │   ├── login.html         # 登录页
│   │   ├── dashboard.html     # 仪表盘
│   │   ├── users.html         # 用户管理
│   │   ├── customers.html     # 顾客管理
│   │   ├── work_repos.html    # 工作日报
│   │   ├── work_repo_sums.html # 工作日报总结
│   │   ├── industry_repos.html # 行业周报
│   │   ├── email.html         # 邮件推送
│   │   ├── text2sql.html      # 智能查询
│   │   └── ai_chat.html       # AI智能助手（流式SSE渲染，Markdown实时渲染，打字光标动画，文件上传，耗时统计）
│   └── static/                # 静态资源
│       ├── css/
│       ├── js/
│       └── live2d/            # Live2D 看板娘资源
│           └── katou/         # 加藤惠模型
│               ├── css/       # 看板娘样式
│               ├── images/    # 功能图标
│               ├── js/        # Live2D SDK + 交互逻辑
│               ├── model/     # 模型数据（moc/纹理/动作/表情/物理/姿势）
│               └── message.json  # 悬停/点击消息配置
├── log/                       # 日志目录
│   ├── app.log               # 应用日志（自动轮转，保留7天）
│   └── app_error.log         # 错误日志（自动轮转，保留7天）
├── .env                      # 环境变量配置
├── requirements.txt          # Python依赖
├── migrate.py                # 数据库迁移脚本
└── README.md
```

## 环境要求

- Python 3.10+
- MySQL 8.0+
- Dify（自部署或云端）

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

# Dify
DIFY_BASE_URL=http://your_dify_server
DIFY_WORK_REPO_SUM_API_KEY=your_work_repo_sum_api_key
DIFY_INDUSTRY_REPO_API_KEY=your_industry_repo_api_key
DIFY_CHAT_API_KEY=your_chat_api_key

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

## UI 主题

前端采用**暗黑系风格主题**，以深蓝紫渐变为基底，搭配粉紫强调色：

| 变量 | 色值 | 用途 |
|------|------|------|
| `--jirai-black` | `#1a1a2e` | 主背景 |
| `--jirai-dark` | `#16213e` | 侧边栏 |
| `--jirai-purple` | `#533483` | 次要强调 |
| `--jirai-pink` | `#e91e63` | 主强调色（按钮/高亮/聚焦） |
| `--jirai-soft-pink` | `#fce4ec` | 标题/高亮文本 |
| `--jirai-lavender` | `#b39ddb` | 辅助文本 |
| `--jirai-text` | `#e1bee7` | 主文本（淡紫粉） |

- **背景**：深蓝紫渐变 `linear-gradient(160deg, #0f0c29, #1a1a2e, #24243e)`
- **卡片**：毛玻璃效果（`backdrop-filter: blur(10px)`）+ 半透明深色 + 紫色边框
- **按钮**：粉紫渐变 `#e91e63 → #533483`，hover 带粉色阴影
- **表格**：深色背景 + 紫色表头 + 斑马纹 + 粉色悬停高亮
- **表单**：半透明深色背景，聚焦时粉色边框 + 粉色光晕
- **滚动条**：自定义深色 + 粉色滑块
- **首页 Hero**：浮动光晕动画 + 粒子背景

## Live2D 看板娘

首页集成 Live2D 看板娘（加藤惠，来自《路人女主的养成方法》），功能包括：

- **时间问候**：根据当前时间段显示不同问候语（深夜/清晨/上午/中午/午后/傍晚/晚上）
- **点击互动**：点击模型显示随机角色语音文本
- **悬停提示**：页面元素悬停时显示对应提示文本（通过 `message.json` 配置）
- **拖拽移动**：支持鼠标拖拽调整位置，位置通过 `sessionStorage` 持久化
- **显示/隐藏**：隐藏按钮退出后显示44px圆形图标按钮（右下角），状态通过 `localStorage` 记忆
- **Dify 聊天联动**：点击看板娘自动触发 Dify 嵌入式聊天窗口
- **淡入淡出**：显示/隐藏带渐变过渡动画
- **移动端适配**：860px 以下自动隐藏
- **模型细节**：6种表情（ANGRY/DOWN/FUN/NOMAL/SAD/SURPRISE）+ 16个动作 + 物理引擎 + 2048分辨率纹理

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
| 工作日报总结 | GET | `/api/work-repo-sums` | 总结列表 |
| 工作日报总结 | GET | `/api/work-repo-sums/{ws_id}` | 总结详情 |
| 工作日报总结 | POST | `/api/work-repo-sums/generate` | AI生成指定日期总结 |
| 工作日报总结 | DELETE | `/api/work-repo-sums/{ws_id}` | 删除总结 |
| 行业周报 | GET | `/api/industry-repos` | 周报列表 |
| 行业周报 | GET | `/api/industry-repos/{i_id}` | 周报详情 |
| 行业周报 | POST | `/api/industry-repos/generate` | AI生成指定日期范围周报 |
| 行业周报 | POST | `/api/industry-repos` | 创建周报 |
| 行业周报 | PUT | `/api/industry-repos/{i_id}` | 更新周报 |
| 行业周报 | DELETE | `/api/industry-repos/{i_id}` | 删除周报 |
| 邮件 | POST | `/api/email/send` | 发送邮件 |
| 智能查询 | POST | `/api/text2sql/query` | 自然语言转SQL查询 |
| AI助手 | POST | `/api/ai-chat/message` | AI对话 - 阻塞模式（支持文件上传） |
| AI助手 | POST | `/api/ai-chat/stream` | AI对话 - 流式SSE模式（实时逐token渲染） |

## 权限说明

| 角色 | role值 | 权限 |
|------|--------|------|
| 管理员 | 0 | 查看所有页面和所有信息，AI生成日报总结和行业周报 |
| 普通员工 | 1 | CRUD所有顾客、CRUD自己的工作日报、CRUD行业周报 |
| 经理 | 2 | CRUD所有顾客、查看所有工作日报、AI生成日报总结和行业周报 |
| 学生 | 3 | 查看与自己关联的顾客 |

## 数据库表

- **users**: 用户表（uid, username, pwd, name, gender, email, phone, role, create_time, is_del）
- **customers**: 顾客表（c_id, c_name, c_age, c_gender, c_phone, c_email, c_degree, c_region, c_suit_project, create_time, update_time, link_uid, c_status, c_rank, c_analyze_info, is_del）
  - `c_rank`: 顾客评级（S/A/B/C/D，S=核心顾客, A=重要顾客, B=普通顾客, C=一般顾客, D=边缘顾客）
  - `c_suit_project`: 适配项目（0=所有项目都符合, 1=都不符合, 2=新加坡国际本硕升学计划, 3=中德精英人才共建计划）
- **work_repo**: 工作日报表（w_id, w_date, w_title, u_id, content, create_time, update_time, is_del）
- **work_repo_sum**: 工作日报总结表（ws_id, ws_date, ws_title, content, create_time, is_del）
- **industry_repo**: 行业周报表（i_id, i_title, content, create_time, is_del）

## AI 功能

### Dify 集成

系统集成 Dify AI 平台，提供以下智能能力：

- **工作日报总结**：调用 Dify Chatbot API，根据指定日期的所有员工日报自动生成总结报告
  - 手动触发：POST `/api/work-repo-sums/generate?ws_date=YYYY-MM-DD`
  - 定时任务：每天 8:00 自动生成昨日工作日报总结
- **行业周报**：调用 Dify Chatbot API，根据指定日期范围自动生成行业周报
  - 手动触发：POST `/api/industry-repos/generate?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD`
  - 定时任务：每周一 8:30 自动生成上周行业周报
- **首页嵌入式聊天**：通过 Dify 官方前端嵌入组件（`embed.min.js`）在首页右下角展示聊天窗口，点击 Live2D 看板娘自动触发
- **AI 聊天助手**（`/ai-chat` 页面）：基于 Dify Chat API 的自定义对话界面
  - 流式模式（推荐）：POST `/api/ai-chat/stream`，SSE 协议逐 token 实时渲染，打字光标动画
  - 阻塞模式（兼容）：POST `/api/ai-chat/message`，适用于定时任务等不需要流式的场景
  - 支持上传图片/文档，AI 自动识别内容
  - 多轮对话：通过 `conversation_id` 保持上下文
  - 前端渲染优化：
    - 流式渲染：`fetch + ReadableStream` 逐 chunk 解析 SSE 事件，AI 每个 token 立即显示
    - 打字光标：流式输出时显示闪烁光标（▍），回答结束后自动消失
    - 表格横向滚动（`.table-wrapper`），蓝色表头 + 斑马纹 + 悬停高亮
    - 代码块深色主题 + 一键复制按钮，HTML 转义防 XSS
    - Markdown 标题/列表/引用/分割线/段落排版优化
    - AI 回复气泡宽度 90%，充分利用空间
    - 请求耗时实时统计

### Text2SQL 智能查询

系统集成阿里云 DashScope（通义千问）的 Text2SQL 功能，支持自然语言转 SQL 查询：

- **中文字段映射**：查询结果表头自动转换为中文显示
- **值翻译**：性别、角色、状态等数字字段自动映射为中文（如 gender: 0→男, 1→女）
- **安全限制**：仅允许 SELECT 查询，自动拦截 INSERT/UPDATE/DELETE/DROP 等危险操作
- **敏感字段过滤**：自动隐藏 `pwd`、`is_del` 等敏感/内部字段
- **SQL注入防护**：过滤注释、拦截危险关键字和文件操作
- **三级权限控制**：
  - **表级权限**：不同角色只能查询允许的表（如学生只能查顾客表）
  - **行级权限**：自动注入 WHERE 条件限制数据范围（如普通员工只能查自己的日报）
  - **列级权限**：按角色过滤结果中的敏感字段（如普通员工不可见 uid/username/email/phone）

#### Text2SQL 权限配置详情

**表级权限**（`ROLE_TABLE_PERMISSIONS`）：

|| 角色 | 允许查询的表 |
||------|-------------|
|| 管理员(0) | 所有表 |
|| 普通员工(1) | customers, work_repo, industry_repo |
|| 经理(2) | users, customers, work_repo, work_repo_sum, industry_repo |
|| 学生(3) | customers |

**行级权限**（`ROLE_ROW_FILTERS`）：

|| 角色 | 表 | 过滤条件 |
||------|-----|---------|
|| 普通员工(1) | work_repo | `u_id = 当前用户uid`（只能查自己的日报） |
|| 学生(3) | customers | `link_uid = 当前用户uid`（只能查关联自己的顾客） |

**列级权限**（`ROLE_HIDDEN_COLUMNS`，结果自动过滤）：

|| 角色 | 隐藏字段 |
||------|---------|
|| 管理员(0) | pwd, is_del |
|| 普通员工(1) | pwd, is_del, uid, username, email, phone |
|| 经理(2) | pwd, is_del |
|| 学生(3) | pwd, is_del, uid, username, email, phone |

## 定时任务

使用 APScheduler（AsyncIOScheduler）实现定时任务：

| 任务 | 执行时间 | 说明 |
|------|----------|------|
| 工作日报总结 | 每天 8:00 | 自动生成昨日工作日报总结 |
| 行业周报 | 每周一 8:30 | 自动生成上周行业周报 |

## 统一异常处理

系统在 `main.py` 中注册了全局异常处理器，确保所有错误返回统一 JSON 格式：

- **HTTPException**：返回标准 JSON 错误响应
- **RequestValidationError**（422）：参数校验失败，返回字段级错误详情
- **全局 Exception**（500）：捕获所有未处理异常，记录错误日志

## 日志系统

- **控制台输出**：带 ANSI 颜色的格式化日志
- **应用日志**：`log/app.log`，按天轮转，保留7天
- **错误日志**：`log/app_error.log`，仅记录 ERROR 级别，按天轮转，保留7天
- **访问日志**：中间件自动记录请求 IP、方法、路径、状态码、处理耗时
- **日志级别**：通过 `.env` 中 `LOG_LEVEL` 配置，默认 `INFO`

## 技术栈

- **后端**: FastAPI + SQLAlchemy + Pydantic
- **认证**: JWT Token + MD5密码加密
- **AI**: Dify（工作日报总结、行业周报生成、AI聊天助手）+ 阿里云DashScope（Text2SQL）
- **邮件**: aiosmtplib + 163邮箱SMTP
- **定时任务**: APScheduler
- **HTTP客户端**: httpx（Dify API调用，全局连接池复用 + 流式SSE）
- **日志**: Python logging + TimedRotatingFileHandler
- **前端**: Bootstrap 5 + Bootstrap Icons + Jinja2模板 + Marked.js v4（Markdown渲染）+ Live2D SDK
- **UI主题**: 暗黑系风格（深蓝紫渐变 + 粉紫强调 + 毛玻璃效果）
- **数据库**: MySQL 8.0
