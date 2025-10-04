from datetime import timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.sql.annotation import Annotated
from starlette import status

from core import verify_password, create_access_token, get_password_hash
from core.config import ACCESS_TOKEN_TTL_MINUTES
from core.dependencies import get_current_active_user, get_current_user, get_current_admin
from dao.dao import UserDAO, AdminDAO, SecretDAO, AccessRequestDAO
from database.models import AccessStatus
from models.user import LoginRequest, Token, AdminResponse, AdminCreate
from openbao_client import OpenBaoClient

secret_router = APIRouter()
client = OpenBaoClient()

async def authenticate_user(username: str, password: str):
    user = await AdminDAO.find_data_by_id(username=username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


@secret_router.post("/login", response_model=Token)
async def login_for_access_token(
        login_data: LoginRequest  # Используем LoginRequest вместо Annotated
):
    user = await authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_TTL_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@secret_router.get("/secret/{path}")
async def get_secret(path: str):
    try:
        secret = client.read_secret(path)
        return {"data": secret["data"]["data"]}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@secret_router.post("/secret/{path}")
async def create_secret(path: str, payload: dict, current_admin : AdminResponse = Depends(get_current_admin)):
    try:
        client.write_secret(path, payload)
        await SecretDAO.add(service_name=path,
                            keys=payload)
        return {"status": "ok", "path": path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@secret_router.get('/requests')
async def get_access_requests(current_admin : AdminResponse = Depends(get_current_admin)):
    return await AccessRequestDAO.find_data_by_id()