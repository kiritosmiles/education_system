import hashlib
from datetime import datetime, timedelta
from jose import jwt, JWTError
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import get_settings
from app.database import get_db
from app.models.user import User
from app.schemas.user import TokenData

settings = get_settings()
security = HTTPBearer()


def md5_hash(text: str) -> str:
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def create_token(uid: int, role: int) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    payload = {"uid": uid, "role": role, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> TokenData:
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        uid = payload.get("uid")
        role = payload.get("role")
        if uid is None:
            raise HTTPException(status_code=401, detail="无效的Token")
        return TokenData(uid=uid, role=role)
    except JWTError:
        raise HTTPException(status_code=401, detail="无效的Token")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    token_data = decode_token(credentials.credentials)
    user = db.query(User).filter(User.uid == token_data.uid, User.is_del == 0).first()
    if not user:
        raise HTTPException(status_code=401, detail="用户不存在")
    return user


def require_role(*roles: int):
    def checker(current_user: User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="权限不足")
        return current_user
    return checker
