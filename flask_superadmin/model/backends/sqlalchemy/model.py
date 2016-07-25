from datetime import datetime

from sqlalchemy_utils import force_auto_coercion, PasswordType

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()

utcnow = datetime.utcnow


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # real_name = Column(String(50))
    username = Column(String(50), unique=True, index=True)
    email = Column(String(50), unique=True, index=True)
    created_at = Column(DateTime, default=utcnow)

    password = Column(PasswordType(
        onload=lambda **kwargs: {
            "schemes": ['pbkdf2_sha512', 'md5_crypt'],
            **kwargs
        },
    ))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return '<User %r>' % (self.username)


