from typing import List, Optional, Dict, Any

from sqlalchemy.orm import Mapped, mapped_column

from database.database import Base, uniq_str_an
from enum import Enum
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Table, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import datetime

class AccessStatus(str, Enum):
    PENDING = 'pending'
    REJECTED = 'rejected'
    APPROVED = 'approved'

class User(Base):

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)

    access_requests: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    access_records: Mapped[List["AccessRecord"]] = relationship(
        "AccessRecord",
        back_populates="user",
        cascade="all, delete-orphan"
    )


class Secret(Base):

    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    keys: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    access_requests: Mapped[List["AccessRequest"]] = relationship(
        "AccessRequest",
        back_populates="secret",
        cascade="all, delete-orphan"
    )
    access_records: Mapped[List["AccessRecord"]] = relationship(
        "AccessRecord",
        back_populates="secret",
        cascade="all, delete-orphan"
    )

    # Связь многие-ко-многим с User через access_records
    users_accessed: Mapped[List["User"]] = relationship(
        "User",
        secondary="access_records",
        primaryjoin="Secret.id == AccessRecord.secret_id",
        secondaryjoin="User.id == AccessRecord.user_id",
        viewonly=True,
        backref="accessed_secrets_view"
    )


class AccessRequest(Base):

    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    access_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[AccessStatus] = mapped_column(String(20), default=AccessStatus.PENDING, nullable=False)
    response_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Внешние ключи
    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey('secrets.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)

    # Связи
    secret: Mapped["Secret"] = relationship("Secret", back_populates="access_requests")
    user: Mapped["User"] = relationship("User", back_populates="access_requests")


class AccessRecord(Base):
    expiration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Внешние ключи
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey('secrets.id'), nullable=False)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="access_records")
    secret: Mapped["Secret"] = relationship("Secret", back_populates="access_records")