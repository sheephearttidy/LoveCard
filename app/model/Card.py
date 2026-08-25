from model.db import db
from sqlalchemy.orm import mapped_column

class Card(db.Model):
    __tablename__ = 'card'
    id = mapped_column(db.Integer, primary_key=True)
