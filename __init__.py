import os
from flask import Flask, jsonify, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import text
from extensions import db
from extensions import cache
from api import api_bp

from middleware_Auth import authenticate
from flask_jwt_extended import JWTManager
from data_models.convertors import WorkoutConverter, SongConverter, WorkoutPlanConverter, PlaylistConverter, UserConverter


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SQLALCHEMY_DATABASE_BASE_URI"] = "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com/workout_playlists"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = 'ireshisthe key'
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "./cache"

app.url_map.converters["workout"] = WorkoutConverter
app.url_map.converters["workoutPlan"] = WorkoutPlanConverter
app.url_map.converters["song"] = SongConverter
app.url_map.converters["playlist"] = PlaylistConverter
app.url_map.converters["user"] = UserConverter

jwt = JWTManager(app)
db.init_app(app)
cache.init_app(app)

def create_database():
    engine = sqlalchemy.create_engine(app.config['SQLALCHEMY_DATABASE_BASE_URI'], echo=True)
    conn = engine.connect()
    try:
        query = "CREATE DATABASE IF NOT EXISTS workout_playlists;"
        conn.execute(text(query))
        print("Database created successfully.")
    except Exception as e:
        print("Error creating database:", e)
    conn.close()

def create_tables():
    db.metadata.create_all(bind=db.engine, checkfirst=True)

with app.app_context():
    create_database()
    db.create_all()

app.register_blueprint(api_bp, url_prefix='/api')
app.before_request(authenticate)
if __name__ == "__main__":
    app.run(debug=True)

def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_BASE_URI="mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com",
        SQLALCHEMY_DATABASE_URI="mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com/workout_playlists",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    app.config['JWT_SECRET_KEY'] = 'ireshisthe key'
    jwt = JWTManager(app)
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.before_request(authenticate)
    db.init_app(app)

    from . import api
    
    app.register_blueprint(api.api_bp, url_prefix='/api')

    return app
