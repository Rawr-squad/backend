from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated

from core.security import verify_token
from dao.dao import UserDAO, AdminDAO
from models.user import UserResponse, AdminResponse

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")

async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
) -> UserResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = await UserDAO.find_by_username(username=username)
    if user is None:
        raise credentials_exception

    # Вручную создаем Pydantic модель из SQLAlchemy модели
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        firstname=user.firstname,
        lastname=user.lastname,
        field=user.position,
        disabled=user.disabled,
        created_at=user.created_at,
        updated_at=user.update_at
    )

async def get_current_active_user(
        current_user: Annotated[UserResponse, Depends(get_current_user)]
) -> UserResponse:
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

async def get_current_admin(
        token: Annotated[str, Depends(oauth2_scheme)],
) -> AdminResponse:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = verify_token(token)
    if payload is None:
        raise credentials_exception

    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception

    user = await AdminDAO.find_data_by_filter(username=username)
    if user is None:
        raise credentials_exception

    # Вручную создаем Pydantic модель из SQLAlchemy модели
    return AdminResponse(
        id=user.id,
        username=user.username,
        created_at=user.created_at,
        update_at=user.update_at,
    )
