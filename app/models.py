from typing import ClassVar
from datetime import datetime, timezone
from flask_sqlalchemy.query import Query
from app import db, login  # type: ignore
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash


class User(UserMixin, db.Model):
    __tablename__ = "users"
    query: ClassVar[Query]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False)
    name = db.Column(db.String(64))
    email = db.Column(db.String(120), unique=True)
    age = db.Column(db.Integer)
    weight = db.Column(db.Float)
    height = db.Column(db.Float)
    fitness_goal = db.Column(db.String(120))
    password_hash = db.Column(db.String(256))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Workout(db.Model):
    __tablename__ = "workouts"
    query: ClassVar[Query]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    duration = db.Column(db.Integer)  # minutes
    calories_burned = db.Column(db.Integer)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class Meal(db.Model):
    __tablename__ = "meals"
    query: ClassVar[Query]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120))
    calories = db.Column(db.Float)
    protein = db.Column(db.Float)
    carbs = db.Column(db.Float)
    fats = db.Column(db.Float)
    meal_type = db.Column(db.String(20), default="Snack")
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))


class Recommendation(db.Model):
    __tablename__ = "ai_recommendations"
    query: ClassVar[Query]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    meal_rec = db.Column(db.String(200))
    workout_rec = db.Column(db.String(200))
    trend_note = db.Column(db.String(255))
    followed = db.Column(db.String(10))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))


class WeightLog(db.Model):
    __tablename__ = "weight_logs"
    query: ClassVar[Query]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    weight = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
