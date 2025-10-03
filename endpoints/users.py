from fastapi import APIRouter

from dao.dao import UserDAO
from models.user import User

user_router = APIRouter()

@user_router.get('/')
async def start_message():
    return {'message' : 'auth_land'}

@user_router.get('/get_user/{user_id}')
async def get_users(user_id : int):
    user = await UserDAO.find_data_by_id(id=user_id)
    return user

@user_router.post('/add_user')
async def add_user(user : User):
    new_user = await UserDAO.add(username=user.username, password=user.password)
    return {"message":"user added successfully", "User" : {new_user}}