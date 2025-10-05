import asyncio
import sys
import os

# Добавляем путь к проекту для импортов
sys.path.append('/app')

from database.database import async_session_maker
from database.models import User
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

# Используем pwdlib
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def get_password_hash(password: str):
    return password_hash.hash(password)


async def create_user_if_not_exists(user_data):
    """Создает пользователя, если он не существует"""
    async with async_session_maker() as session:
        # Проверяем существование пользователя
        query = select(User).where(User.username == user_data["username"])
        result = await session.execute(query)
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"User '{user_data['username']}' already exists")
            return False

        # Создаем пользователя
        new_user = User(
            username=user_data["username"],
            password_hash=get_password_hash(user_data["password"]),
            firstname=user_data["firstname"],
            lastname=user_data["lastname"],
            email=user_data.get("email"),
            position=user_data.get("position"),
            disabled=False
        )

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)

        print(f"User '{user_data['username']}' created successfully")
        return True


async def create_test_users():
    """Создает тестовых пользователей"""
    test_users = [
        {
            "username": "valdemar",
            "firstname": "volodya",
            "lastname": "baranov",
            "password": "baranov123123123",
            "email": "valdemar@example.com",
            "position": "Development"
        },
        {
            "username": "galina",
            "firstname": "galya",
            "lastname": "sergeevna",
            "password": "galya12321",
            "email": "galina@example.com",
            "position": "Management"
        }
    ]

    created_count = 0
    for user_data in test_users:
        if await create_user_if_not_exists(user_data):
            created_count += 1

    if created_count > 0:
        print("=" * 50)
        print(f"SUCCESSFULLY CREATED {created_count} TEST USERS")
        print("Available test users:")
        for user in test_users:
            print(f"   - Username: {user['username']}")
            print(f"     Password: {user['password']}")
        print("=" * 50)
    else:
        print("ℹAll test users already exist")


async def main():
    """Основная функция"""
    # Ждем подключения к БД
    max_retries = 10
    for i in range(max_retries):
        try:
            async with async_session_maker() as session:
                await session.execute(select(1))
                print("Database connection successful")
                break
        except SQLAlchemyError:
            if i < max_retries - 1:
                print(f"Waiting for database... ({i + 1}/{max_retries})")
                await asyncio.sleep(2)
            else:
                print("Database connection failed")
                return

    # Создаем тестовых пользователей
    await create_test_users()


if __name__ == "__main__":
    asyncio.run(main())