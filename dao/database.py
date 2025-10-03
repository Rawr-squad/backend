from typing import Annotated

from sqlalchemy import Integer
from sqlalchemy.orm import DeclarativeBase, declared_attr, class_mapper, mapped_column, Mapped

from core.config import get_db_url
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs

DATABASE_URL = get_db_url()

engine = create_async_engine(url=DATABASE_URL)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

print(DATABASE_URL)

uniq_str_an = Annotated[str, mapped_column(unique=True)]

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    id : Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    # update_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @declared_attr.directive
    def __tablename__(cls) -> str :
        return cls.__name__.lower() + 's'

    def to_dict(self) -> dict :
        columns = class_mapper(self.__class__).columns
        return {column.key : getattr(self, column.key) for column in columns}