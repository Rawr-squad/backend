from datetime import timedelta, datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.sql.annotation import Annotated
from starlette import status

from core import verify_password, create_access_token, get_password_hash
from core.config import ACCESS_TOKEN_TTL_MINUTES
from core.dependencies import get_current_active_user, get_current_user, get_current_admin
from dao.dao import UserDAO, AdminDAO, SecretDAO, AccessRequestDAO, AccessRecordDAO
from database.models import AccessStatus
from models.secrets import ChangeStatusRequest
from models.user import LoginRequest, Token, AdminResponse, AdminCreate, UserResponse
from openbao_client import OpenBaoClient

secret_router = APIRouter()
client = OpenBaoClient()

async def authenticate_user(username: str, password: str):
    user = await AdminDAO.find_data_by_filter(username=username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


@secret_router.post("/login", response_model=Token)
async def login_for_access_token(
        login_data: LoginRequest
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
async def get_secret(
        path: str,
        current_user: UserResponse = Depends(get_current_active_user)
):
    try:
        secret_record = await SecretDAO.find_by_path(path)
        if not secret_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Secret '{path}' not found"
            )

        active_access = await AccessRecordDAO.get_active_access(
            user_id=current_user.id,
            secret_id=secret_record.id
        )

        if not active_access:
            any_access = await AccessRecordDAO.find_data_by_filter(
                user_id=current_user.id,
                secret_id=secret_record.id
            )

            if any_access:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access expired"
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied - no permissions"
                )

        # Получаем секрет из OpenBao/Vault
        secret = client.read_secret(path)
        return {
            "data": secret["data"]["data"],
            "access_info": {
                "expires_at": active_access.expiration_date.isoformat(),
                "access_record_id": active_access.id
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@secret_router.put("/secret/{path}")
async def create_secret(path: str, payload: dict, current_admin : AdminResponse = Depends(get_current_admin)):
    data = await SecretDAO.find_data_by_filter(service_name=path)
    if not data:
        try:
            client.write_secret(path, payload)
            await SecretDAO.add(service_name=path,
                                keys=list(payload.keys()))
            return {"status": "ok", "path": path}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else : raise HTTPException(status_code=400, detail="current path already exist")


import asyncio
from typing import Optional


@secret_router.get("/requests")
async def get_access_requests(
    timeout: int = 30,
    last_update: Optional[str] = None,
    status: Optional[AccessStatus] = Query(
        None,
        description="Фильтрация по статусу: approved, rejected, pending"
    ),
    current_admin: AdminResponse = Depends(get_current_admin)
):
    """
    Long polling эндпоинт для получения access requests.
    Можно фильтровать по статусу (approved/rejected/pending).
    """

    start_time = asyncio.get_event_loop().time()

    while True:
        # Получаем текущие запросы
        current_requests = await AccessRequestDAO.find_all()

        # фильтрация по статусу, если задан query параметр
        if status:
            current_requests = [
                req for req in current_requests if req.status == status
            ]

        # Проверяем наличие last_update
        if last_update:
            try:
                last_update_dt = datetime.fromisoformat(last_update.replace("Z", "+00:00"))
                changed_requests = [
                    req for req in current_requests
                    if req.update_at > last_update_dt
                ]

                if changed_requests:
                    return {
                        "requests": current_requests,
                        "last_update": datetime.now().isoformat(),
                        "has_changes": True
                    }
            except ValueError:
                return {
                    "requests": current_requests,
                    "last_update": datetime.now().isoformat(),
                    "has_changes": True
                }
        else:
            return {
                "requests": current_requests,
                "last_update": datetime.now().isoformat(),
                "has_changes": True
            }

        # Проверяем таймаут
        elapsed_time = asyncio.get_event_loop().time() - start_time
        if elapsed_time >= timeout:
            return {
                "requests": current_requests,
                "last_update": last_update or datetime.now().isoformat(),
                "has_changes": False,
                "timeout": True
            }

        await asyncio.sleep(2)

@secret_router.post('/requests/change_status')
async def change_status_access_request(
        change_data: ChangeStatusRequest,  # Принимаем данные из тела запроса
        current_admin: AdminResponse = Depends(get_current_admin)
):
    """Изменить статус запроса доступа и создать AccessRecord при одобрении"""

    # Находим запрос
    access_request = await AccessRequestDAO.find_one(id=change_data.request_id)
    if not access_request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Access request not found"
        )

    # Проверяем, не одобрен ли уже этот запрос
    if access_request.status == AccessStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This request is already approved"
        )

    # Обновляем статус
    updated_request = await AccessRequestDAO.update_status(
        request_id=change_data.request_id,
        status=change_data.new_status,
        response_message=change_data.response_message
    )

    response_data = {
        "message": f"Access request status updated to {change_data.new_status.value}",
        "request": updated_request
    }

    # Если статус APPROVED - создаем запись в AccessRecord
    if change_data.new_status == AccessStatus.APPROVED:
        # Проверяем, нет ли уже активного доступа
        existing_access = await AccessRecordDAO.find_active_by_user_and_secret(
            user_id=access_request.user_id,
            secret_id=access_request.secret_id
        )

        if existing_access:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has active access to this secret"
            )

        # Вычисляем дату истечения
        expiration_date = datetime.now() + timedelta(days=access_request.access_period)

        # Создаем запись о доступе
        access_record = await AccessRecordDAO.add(
            user_id=access_request.user_id,
            secret_id=access_request.secret_id,
            expiration_date=expiration_date
        )

        if not access_record:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create access record"
            )

        response_data.update({
            "message": "Access request approved and access record created",
            "access_record": access_record,
            "expires_at": expiration_date.isoformat()
        })

    return response_data
