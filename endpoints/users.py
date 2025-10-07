from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from core.security import verify_password, create_access_token, get_password_hash
from core.config import ACCESS_TOKEN_TTL_MINUTES
from core.dependencies import get_current_active_user
from dao.dao import UserDAO, AccessRequestDAO, SecretDAO, AccessRecordDAO
from database.models import AccessRequest, AccessStatus
from models.user import UserResponse, UserCreate, Token, LoginRequest, AccessRequestModel

user_router = APIRouter()


@user_router.get('/')
async def start_message():
    return {'message': 'auth_land'}


@user_router.get('/get_user/{user_id}', response_model=UserResponse)
async def get_users(user_id: int):
    user = await UserDAO.find_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        field=user.position,
        disabled=user.disabled,
        created_at=user.created_at,
        updated_at=user.updated_at
    )


@user_router.post('/register', response_model=UserResponse)
async def add_user(user: UserCreate):
    # Проверяем, существует ли пользователь
    existing_user = await UserDAO.find_by_username(user.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    password_hash = get_password_hash(password=user.password)

    new_user = await UserDAO.create_user(
        username=user.username,
        password_hash=password_hash,
        firstname=user.firstname,
        lastname=user.lastname,
        email=user.email,
        field=user.field
    )

    if not new_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

    return UserResponse(
        id=new_user.id,
        username=new_user.username,
        email=new_user.email,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        field=new_user.position,
        disabled=new_user.disabled,
        created_at=new_user.created_at,
        updated_at=new_user.update_at
    )


async def authenticate_user(username: str, password: str):
    user = await UserDAO.find_by_username(username=username)
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user


@user_router.post("/login", response_model=Token)
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


@user_router.get("/me/", response_model=UserResponse)
async def read_users_me(
        current_user: Annotated[UserResponse, Depends(get_current_active_user)],
):
    return current_user


@user_router.post('/access')
async def send_access_request(
        model: AccessRequestModel,
        current_user: Annotated[UserResponse, Depends(get_current_active_user)]
):
    secret = await SecretDAO.find_data_by_filter(id=model.secret_id)
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Secret not found"
        )
    # Проверяем, есть ли уже pending запрос
    has_pending = await AccessRequestDAO.has_pending_request(
        user_id=current_user.id,
        secret_id=model.secret_id
    )

    if has_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a pending access request for this secret. Please wait for the current request to be processed."
        )

    # Также можно проверить, есть ли уже approved запрос
    existing_approved_request = await AccessRequestDAO.find_one(
        user_id=current_user.id,
        secret_id=model.secret_id,
        status=AccessStatus.APPROVED
    )

    if existing_approved_request:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have approved access to this secret"
        )

    # Создаем новый запрос
    new_access = await AccessRequestDAO.add(
        request_data=model.request_data,
        access_period=model.access_period,
        access_reason=model.access_reason,
        secret_id=model.secret_id,
        user_id=current_user.id,
        status=AccessStatus.PENDING
    )

    if not new_access:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create access request"
        )

    return new_access


@user_router.get('/secrets')
async def get_access_secrets(current_user: Annotated[UserResponse, Depends(get_current_active_user)]):
    return await SecretDAO.find_data_by_filter()


@user_router.get('/allowed_secrets')
async def get_access_secrets(current_user: Annotated[UserResponse, Depends(get_current_active_user)]):
    return await AccessRecordDAO.find_active_by_user(user_id=current_user.id)
