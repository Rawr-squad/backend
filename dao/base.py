from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from database.database import async_session_maker, Base
from typing import Generic, TypeVar

T = TypeVar("T", bound=Base)


class BaseDAO(Generic[T]):
    model = type[T]

    @classmethod
    async def add(cls, **values):
        async with async_session_maker() as session:
            new_instance = cls.model(**values)
            session.add(new_instance)
            try:
                await session.commit()
            except SQLAlchemyError as e:
                await session.rollback()
                raise e
            return new_instance

    @classmethod
    async def find_data_by_id(cls, **filtered_by):
        async with async_session_maker() as session:
            if filtered_by:
                query = select(cls.model).filter_by(**filtered_by)
                result = await session.execute(query)
                record = result.scalar()
            else:
                query = select(cls.model)
                result = await session.execute(query)
                record = result.scalars().all()
            return record


