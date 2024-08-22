"""SQLAlchemy models for Spontinerary."""
from datetime import datetime
from sqlalchemy.sql import func

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User"""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String, nullable=False, unique=True)
    image_url = db.Column(db.Text, default="/static/images/default-pic.png")
    password = db.Column(db.String, nullable=False )
    
    itineraries = db.relationship('Itinerary', backref='user', cascade="all, delete-orphan")
    activities = db.relationship('Activity', backref='user', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User #{self.id}: {self.username}>"

    @classmethod
    def register(cls, username, email, password, image_url):
        """Registers the user with hashed password and returns the user"""
        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Validate that the user exists and the password is correct. Returns the user if valid, else, return false"""
        user = cls.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password, password):
            return user
        return False


class Itinerary(db.Model):
    """An itinerary owned by a user"""

    __tablename__ = 'itineraries'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, nullable=False)
    location = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    radius = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    
    def add_activities(self, activities):
        """Add activities into the itinerary"""
        for activity in activities:
            self.activities.append(activity)
    
    activities = db.relationship('Activity', backref='itinerary', cascade="all, delete-orphan")


class Activity(db.Model):
    """An activity from the itinerary."""

    __tablename__ = 'activities'

    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(db.Integer, db.ForeignKey('itineraries.id', ondelete='CASCADE'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    title = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(20), nullable=False)
    activity_url = db.Column(db.String)
    address = db.Column(db.String)
    summary = db.Column(db.Text)
    

def connect_db(app):
    """Connect this db"""
    db.app = app
    db.init_app(app)
