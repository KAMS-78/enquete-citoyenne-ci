# -*- coding: utf-8 -*-

import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-me'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///database.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_URL_PATH = 'x7Qm9Vz2Lp4Nk8R'
    ADMIN_PASSWORD = 'CHANGE_ME_IN_PRODUCTION'