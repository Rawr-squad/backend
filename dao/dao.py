from dao.base import BaseDAO
from database.models import User

class UserDAO(BaseDAO[User]):
    model = User
