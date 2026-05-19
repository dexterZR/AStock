from fastapi import APIRouter, HTTPException, Response
import asyncio
from datetime import datetime, timedelta
import bcrypt, jwt
from pydantic import BaseModel, field_validator
from app.core.config import settings
from app.api.deps import get_db
from motor.motor_asyncio import AsyncIOMotorDatabase
from fastapi import Depends

router = APIRouter(prefix="/api/auth", tags=["认证"])


class RegisterRequest(BaseModel):
    username: str
    password: str

    @field_validator('username')
    @classmethod
    def username_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError('用户名不能为空')
        if len(v) < 2:
            raise ValueError('用户名至少2个字符')
        return v

    @field_validator('password')
    @classmethod
    def password_strong(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError('密码至少8个字符')
        if not any(c.isupper() for c in v):
            raise ValueError('密码需包含至少一个大写字母')
        if not any(c.islower() for c in v):
            raise ValueError('密码需包含至少一个小写字母')
        if not any(c.isdigit() for c in v):
            raise ValueError('密码需包含至少一个数字')
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    username: str
    token_type: str = 'bearer'


@router.post("/register")
async def register(body: RegisterRequest, db: AsyncIOMotorDatabase = Depends(get_db)):
    existing = await db["users"].find_one({"username": body.username})
    if existing:
        raise HTTPException(400, "用户名已存在")
    hashed = await asyncio.to_thread(bcrypt.hashpw, body.password.encode(), bcrypt.gensalt())
    await db["users"].insert_one({
        "username": body.username,
        "password": hashed.decode(),
        "created_at": datetime.now().isoformat(),
    })
    return {"message": "注册成功"}


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, response: Response, db: AsyncIOMotorDatabase = Depends(get_db)):
    user = await db["users"].find_one({"username": body.username.strip()})
    if not user or not await asyncio.to_thread(bcrypt.checkpw, body.password.encode(), user["password"].encode()):
        raise HTTPException(401, "用户名或密码错误")
    payload = {
        "user_id": str(user["_id"]),
        "username": body.username.strip(),
        "exp": datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRE_HOURS),
    }
    token = jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")
    # 设置 httpOnly Cookie 用于 SSE 等不支持自定义 Header 的场景
    response.set_cookie(
        key="astock_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=settings.JWT_EXPIRE_HOURS * 3600,
        path="/",
    )
    return TokenResponse(access_token=token, username=body.username.strip())
