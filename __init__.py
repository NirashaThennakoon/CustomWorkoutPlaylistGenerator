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

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config["SQLALCHEMY_DATABASE_BASE_URI"] = "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com"
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com/workout_playlists"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['JWT_SECRET_KEY'] = 'ireshisthe key'
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "./cache"

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
