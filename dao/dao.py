from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from dao.base import BaseDAO
from database.models import User, Secret, Admin, AccessRequest, AccessStatus
from database.database import async_session_maker


class UserDAO(BaseDAO):
    model = User

    @classmethod
    async def find_by_username(cls, username: str) -> Optional[User]:
        """Найти пользователя по username"""
        try:
            return await cls.find_data_by_id(username=username)
        except SQLAlchemyError as e:
            print(f"Error finding user by username {username}: {e}")
            return None

    @classmethod
    async def find_by_email(cls, email: str) -> Optional[User]:
        """Найти пользователя по email"""
        try:
            return await cls.find_data_by_id(email=email)
        except SQLAlchemyError as e:
            print(f"Error finding user by email {email}: {e}")
            return None

    @classmethod
    async def find_all(cls) -> List[User]:
        """Найти всех пользователей"""
        try:
            async with async_session_maker() as session:
                query = select(cls.model)
                result = await session.execute(query)
                return result.scalars().all()
        except SQLAlchemyError as e:
            print(f"Error finding all users: {e}")
            return []

    @classmethod
    async def find_by_id(cls, user_id: int) -> Optional[User]:
        """Найти пользователя по ID"""
        try:
            return await cls.find_data_by_id(id=user_id)
        except SQLAlchemyError as e:
            print(f"Error finding user by id {user_id}: {e}")
            return None

    @classmethod
    async def create_user(cls, **user_data) -> Optional[User]:
        """Создать нового пользователя"""
        try:
            return await cls.add(**user_data)
        except SQLAlchemyError as e:
            print(f"Error creating user: {e}")
            return None

    @classmethod
    async def user_exists(cls, username: str, email: str = None) -> bool:
        """Проверить, существует ли пользователь с таким username или email"""
        try:
            # Проверяем по username
            user_by_username = await cls.find_by_username(username)
            if user_by_username:
                return True

            # Если передан email, проверяем и по нему
            if email:
                user_by_email = await cls.find_by_email(email)
                if user_by_email:
                    return True

            return False
        except SQLAlchemyError as e:
            print(f"Error checking if user exists: {e}")
            return False


class SecretDAO(BaseDAO[Secret]):
    model = Secret


class AdminDAO(BaseDAO[Admin]):
    model = Admin


class AccessRequestDAO(BaseDAO[AccessRequest]):
    model = AccessRequest

    @classmethod
    async def has_pending_request(cls, user_id: int, secret_id: int) -> bool:
        """Проверить, есть ли pending запрос у пользователя для секрета"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(
                user_id=user_id,
                secret_id=secret_id,
                status=AccessStatus.PENDING
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None

    @classmethod
    async def find_one(cls, **filters):
        """Найти ОДНУ запись по фильтру (первую найденную)"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(**filters)
            result = await session.execute(query)
            return result.scalar_one_or_none()