from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List

from dao.base import BaseDAO
from database.models import User, Secret, Admin, AccessRequest, AccessStatus, AccessRecord
from database.database import async_session_maker


class UserDAO(BaseDAO[User]):
    model = User

    @classmethod
    async def find_by_username(cls, username: str) -> Optional[User]:
        """Найти пользователя по username"""
        try:
            return await cls.find_data_by_filter(username=username)
        except SQLAlchemyError as e:
            print(f"Error finding user by username {username}: {e}")
            return None

    @classmethod
    async def find_by_id(cls, user_id: int) -> Optional[User]:
        """Найти пользователя по ID"""
        try:
            return await cls.find_data_by_filter(id=user_id)
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


class SecretDAO(BaseDAO[Secret]):
    model = Secret

    @classmethod
    async def find_by_path(cls, path: str) -> Optional[Secret]:
        """Найти секрет по path (service_name)"""
        return await cls.find_data_by_filter(service_name=path)


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

    @classmethod
    async def update(cls, instance_id: int, **values):
        """Обновить запись по ID"""
        async with async_session_maker() as session:
            try:
                # Находим запись
                query = select(cls.model).filter_by(id=instance_id)
                result = await session.execute(query)
                instance = result.scalar_one_or_none()

                if not instance:
                    return None

                # Обновляем поля
                for key, value in values.items():
                    if hasattr(instance, key):
                        setattr(instance, key, value)

                session.add(instance)
                await session.commit()
                await session.refresh(instance)
                return instance

            except SQLAlchemyError as e:
                await session.rollback()
                print(f"Error updating record: {e}")
                raise e

    @classmethod
    async def update_status(cls, request_id: int, status: AccessStatus, response_message: str = None):
        """Обновить статус запроса доступа"""
        update_data = {"status": status}
        if response_message:
            update_data["response_message"] = response_message

        return await cls.update(request_id, **update_data)

    @classmethod
    async def find_all(cls, **filters) -> List[AccessRequest]:
        """Найти все записи с фильтрацией"""
        async with async_session_maker() as session:
            query = select(cls.model)
            if filters:
                query = query.filter_by(**filters)
            # Сортируем по дате обновления (новые сначала)
            query = query.order_by(cls.model.update_at.desc())
            result = await session.execute(query)
            return result.scalars().all()


class AccessRecordDAO(BaseDAO[AccessRecord]):
    model = AccessRecord

    @classmethod
    async def find_active_by_user_and_secret(cls, user_id: int, secret_id: int) -> Optional[AccessRecord]:
        """Найти активную запись доступа (не истекшую)"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(
                user_id=user_id,
                secret_id=secret_id
            ).where(cls.model.expiration_date > datetime.now())

            result = await session.execute(query)
            return result.scalar_one_or_none()

    @classmethod
    async def find_active_by_user(cls, user_id: int) -> List[AccessRecord]:
        """Найти все активные записи доступа пользователя"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(
                user_id=user_id
            ).where(cls.model.expiration_date > datetime.now())

            result = await session.execute(query)
            return result.scalars().all()

    @classmethod
    async def get_active_access(cls, user_id: int, secret_id: int) -> Optional[AccessRecord]:
        """Получить активную запись доступа"""
        async with async_session_maker() as session:
            query = select(cls.model).filter_by(
                user_id=user_id,
                secret_id=secret_id
            ).where(cls.model.expiration_date > datetime.now())

            result = await session.execute(query)
            return result.scalar_one_or_none()
