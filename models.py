# -*- coding: utf-8 -*-

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import secrets

db = SQLAlchemy()

def generate_token():
    return secrets.token_urlsafe(32)

class Respondent(db.Model):
    __tablename__ = 'respondents'
    
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, default=generate_token, nullable=False)
    age = db.Column(db.String(10))
    commune = db.Column(db.String(100))
    education = db.Column(db.String(50))
    smartphone = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started = db.Column(db.Boolean, default=False)
    completed = db.Column(db.Boolean, default=False)
    
    activities = db.relationship('RespondentActivity', backref='respondent', lazy=True)
    problems = db.relationship('Problem', backref='respondent', lazy=True)

class RespondentActivity(db.Model):
    __tablename__ = 'respondent_activities'
    
    id = db.Column(db.Integer, primary_key=True)
    respondent_id = db.Column(db.Integer, db.ForeignKey('respondents.id'), nullable=False)
    activity = db.Column(db.String(50), nullable=False)

class Problem(db.Model):
    __tablename__ = 'problems'
    
    id = db.Column(db.Integer, primary_key=True)
    respondent_id = db.Column(db.Integer, db.ForeignKey('respondents.id'), nullable=False)
    description = db.Column(db.Text)
    situation = db.Column(db.Text)
    current_solution = db.Column(db.Text)
    frequency = db.Column(db.String(50))
    severity = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)