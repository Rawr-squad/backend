import asyncio
import sys
import os

# Добавляем путь к проекту для импортов
sys.path.append('/app')

from database.database import async_session_maker
from database.models import User, Admin
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

# Используем pwdlib
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def get_password_hash(password: str):
    return password_hash.hash(password)


async def wait_for_db():
    """Ждем, пока база данных станет доступной"""
    max_retries = 10
    for i in range(max_retries):
        try:
            async with async_session_maker() as session:
                await session.execute(select(1))
                print("Database connection successful")
                return True
        except SQLAlchemyError:
            if i < max_retries - 1:
                print(f"Waiting for database... ({i + 1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                print("Database connection failed")
                return False


async def create_admin():
    if not await wait_for_db():
        return

    username = "admin"
    password = "root"

    try:
        async with async_session_maker() as session:
            # Проверяем существование админа
            query = select(Admin).where(Admin.username == username)
            result = await session.execute(query)
            existing_admin = result.scalar_one_or_none()

            if existing_admin:
                print(f"Admin user '{username}' already exists")
                return

            # Создаем админа
            admin_user = Admin(
                username=username,
                password_hash=get_password_hash(password),
            )

            session.add(admin_user)
            await session.commit()
            await session.refresh(admin_user)

            print("ADMIN USER CREATED SUCCESSFULLY")
            print(f"Username: {username}")
            print(f"Password: {password}")

    except SQLAlchemyError as e:
        print(f"Error creating admin user: {e}")


if __name__ == "__main__":
    asyncio.run(create_admin())