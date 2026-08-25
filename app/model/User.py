from model.db import db
from sqlalchemy.orm import mapped_column

class User(db.Model):
    __tablename__ = 'user'
    id = mapped_column(db.Integer, primary_key=True,autoincrement=True)
    username = mapped_column(db.String(80), unique=True, nullable=False)
    email = mapped_column(db.String(120), unique=True, nullable=True)
    password = mapped_column(db.String(200), unique=True, nullable=False)