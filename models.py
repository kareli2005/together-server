from flask_sqlalchemy import SQLAlchemy
from uuid import uuid4
from datetime import datetime

db = SQLAlchemy()

def get_uuid():
    return uuid4().hex

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    email = db.Column(db.String(345), unique=True)
    username = db.Column(db.String(345), nullable=False)
    password = db.Column(db.Text, nullable=False)
    profile_picture = db.Column(db.String(255))
    date_joined = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # Relationships
    sent_messages = db.relationship('Messages', foreign_keys='Messages.sender_id', backref='sender', lazy='dynamic')
    received_messages = db.relationship('Messages', foreign_keys='Messages.recipient_id', backref='recipient', lazy='dynamic')

class Messages(db.Model):
    __tablename__ = 'message'
    id = db.Column(db.String(32), primary_key=True, unique=True, default=get_uuid)
    text = db.Column(db.Text)
    date = db.Column(db.DateTime, nullable=False, default=datetime.now)
    sender_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.String(32), db.ForeignKey('user.id'), nullable=False)
