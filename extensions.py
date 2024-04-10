"""
   This module responsible for cache and db global initialization
"""
from flask_sqlalchemy import SQLAlchemy
from flask_caching import Cache

db = SQLAlchemy()
cache = Cache()
