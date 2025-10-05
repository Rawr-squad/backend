from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Boolean, Integer, Text, JSON, ForeignKey, DateTime
from sqlalchemy.sql import func
from database.database import Base
from enum import Enum


class AccessStatus(str, Enum):
    PENDING = 'pending'
    REJECTED = 'rejected'
    APPROVED = 'approved'


class User(Base):

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    firstname: Mapped[str] = mapped_column(String(100), nullable=False)
    lastname: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), unique=True, index=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    disabled: Mapped[bool] = mapped_column(Boolean, default=False)
    position: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class Admin(Base):

    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)


class Secret(Base):

    service_name: Mapped[str] = mapped_column(String(100), nullable=False)
    keys: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)


class AccessRequest(Base):

    request_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    access_period: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    access_reason: Mapped[str] = mapped_column(String(250), nullable=True)
    status: Mapped[AccessStatus] = mapped_column(String(20), default=AccessStatus.PENDING, nullable=False)
    response_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey('secrets.id'), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)


class AccessRecord(Base):

    expiration_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), nullable=False)
    secret_id: Mapped[int] = mapped_column(Integer, ForeignKey('secrets.id'), nullable=False)