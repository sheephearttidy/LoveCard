import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from flask_migrate import Migrate
from app import app
from model import db, User, Card, Comment, Good, Images, System, Tags, TagsMap

migrate = Migrate(app, db)