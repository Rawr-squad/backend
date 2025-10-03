from sqlalchemy.orm import Mapped

from database.database import Base, uniq_str_an


class User(Base):

    username : Mapped[uniq_str_an]
    password : Mapped[uniq_str_an]