import os
import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException

from app.database import engine, Base
from app.middleware import setup_logging, LoggingMiddleware
from app.controllers.auth_controller import router as auth_router
from app.controllers.user_controller import router as user_router
from app.controllers.customer_controller import router as customer_router
from app.controllers.work_repo_controller import router as work_repo_router
from app.controllers.industry_repo_controller import router as industry_repo_router
from app.controllers.email_controller import router as email_router
from app.controllers.text2sql_controller import router as text2sql_router
from app.controllers.work_repo_sum_controller import router as work_repo_sum_router

# 初始化日志
setup_logging()

BASE_DIR = Path(__file__).resolve().parent

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Education System", version="1.0.0")


# ============ 统一异常处理 ============
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": exc.detail, "data": None},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    msg = "; ".join(f"{e.get('loc',[])[-1]}: {e['msg']}" for e in errors)
    return JSONResponse(
        status_code=422,
        content={"code": 422, "msg": msg, "data": None},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"code": 500, "msg": "服务器内部错误", "data": None},
    )

# 注册日志中间件
app.add_middleware(LoggingMiddleware)

# Static files & templates
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# API routers
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(customer_router)
app.include_router(work_repo_router)
app.include_router(industry_repo_router)
app.include_router(email_router)
app.include_router(text2sql_router)
app.include_router(work_repo_sum_router)


# ============ Frontend Pages ============
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "home.html")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")


@app.get("/users", response_class=HTMLResponse)
async def users_page(request: Request):
    return templates.TemplateResponse(request, "users.html")


@app.get("/customers", response_class=HTMLResponse)
async def customers_page(request: Request):
    return templates.TemplateResponse(request, "customers.html")


@app.get("/work-repos", response_class=HTMLResponse)
async def work_repos_page(request: Request):
    return templates.TemplateResponse(request, "work_repos.html")


@app.get("/industry-repos", response_class=HTMLResponse)
async def industry_repos_page(request: Request):
    return templates.TemplateResponse(request, "industry_repos.html")


@app.get("/email", response_class=HTMLResponse)
async def email_page(request: Request):
    return templates.TemplateResponse(request, "email.html")


@app.get("/text2sql", response_class=HTMLResponse)
async def text2sql_page(request: Request):
    return templates.TemplateResponse(request, "text2sql.html")


@app.get("/ai-chat", response_class=HTMLResponse)
async def ai_chat_page(request: Request):
    return templates.TemplateResponse(request, "ai_chat.html")


@app.get("/work-repo-sums", response_class=HTMLResponse)
async def work_repo_sums_page(request: Request):
    return templates.TemplateResponse(request, "work_repo_sums.html")


# ============ 定时任务 ============
@app.on_event("startup")
async def startup_event():
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from app.controllers.work_repo_sum_controller import scheduled_generate_work_repo_sum
    scheduler = AsyncIOScheduler()
    # 每天8:00生成昨日工作日报总结
    scheduler.add_job(scheduled_generate_work_repo_sum, 'cron', hour=8, minute=0)
    scheduler.start()
    app.state.scheduler = scheduler


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
