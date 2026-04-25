import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.user import UserLogin
from app.schemas.common import ResponseBase
from app.utils.auth import md5_hash, create_token, get_current_user
from app.utils.dify_client import chat_message

router = APIRouter(prefix="/api/auth", tags=["认证"])
logger = logging.getLogger(__name__)


@router.post("/login")
async def login(data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    if user.pwd != md5_hash(data.pwd):
        raise HTTPException(status_code=400, detail="用户名或密码错误")
    token = create_token(user.uid, user.role)
    # 登录成功后调用Dify
    try:
        logger.info(f"登录成功，准备调用Dify: uid={user.uid}, token={token[:20]}...")
        result = await chat_message(
            query="用户登录认证成功",
            user=f"uid_{user.uid}",
            inputs={},
            uid=str(user.uid),
            token=token
        )
        logger.info(f"Dify调用成功: answer={result.get('answer', '')[:100]}")
    except Exception as e:
        logger.error(f"登录时调用Dify失败: {e}")
    return ResponseBase(data={
        "token": token,
        "uid": user.uid,
        "username": user.username,
        "name": user.name,
        "role": user.role
    })


@router.get("/info")
def get_info(current_user: User = Depends(get_current_user)):
    return ResponseBase(data={
        "uid": current_user.uid,
        "username": current_user.username,
        "name": current_user.name,
        "role": current_user.role,
        "gender": current_user.gender,
        "email": current_user.email,
        "phone": current_user.phone
    })
