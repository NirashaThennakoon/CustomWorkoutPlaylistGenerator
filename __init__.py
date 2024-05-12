"""
   This module responsible for all initial configurations
"""
import json
import os
import yaml
from flask import Flask, Response, jsonify, render_template, request
from flask_restful import Api, Resource
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from sqlalchemy import text
from flask_jwt_extended import JWTManager
from flasgger import Swagger
from extensions import db, cache
from api import api_bp
from middleware_Auth import authenticate
from data_models.convertors import WorkoutConverter, SongConverter, WorkoutPlanConverter, PlaylistConverter, UserConverter
from flask_cors import CORS

def create_app(test_config=None):
    """
        Create and configure the Flask application.
    """
    app = Flask(__name__, instance_relative_config=True)
    CORS(app, resources={r"/api/*": {"origins": "*", "allow_headers": ["Content-Type", "Authorization", "X-API-Key"], "supports_credentials": True}})

    @app.route('/playlist_link_relation')
    def playlist_link_relation():
        return render_template('playlist_link_relation.html')

    @app.route('/song_link_relation')
    def song_link_relation():
        return render_template('song_link_relation.html')

    @app.route('/user_link_relation')
    def user_link_relation():
        return render_template('user_link_relation.html')

    @app.route('/workout_link_relation')
    def workout_link_relation():
        return render_template('workout_link_relation.html')

    @app.route('/workout_plan_link_relation')
    def workout_plan_link_relation():
        return render_template('workout_plan_link_relation.html')

    @app.route('/profile')
    def profile():
        return render_template('profile.html')
    
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            # Add CORS headers to the response
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
    
    app.config.from_mapping(
        SQLALCHEMY_DATABASE_BASE_URI=
        "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com",
        SQLALCHEMY_DATABASE_URI=
        "mysql+mysqldb://admin:pwpdb7788@workoutplaylists.cpcoaea0i7dq.us-east-1.rds.amazonaws.com/workout_playlists",
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )
    app.config['JWT_SECRET_KEY'] = 'ireshisthe key'
    app.config["CACHE_TYPE"] = "FileSystemCache"
    app.config["CACHE_DIR"] = "./cache"

    app.url_map.converters["workout"] = WorkoutConverter
    app.url_map.converters["workoutPlan"] = WorkoutPlanConverter
    app.url_map.converters["song"] = SongConverter
    app.url_map.converters["playlist"] = PlaylistConverter
    app.url_map.converters["user"] = UserConverter
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
    cache.init_app(app)
    CORS(app)

    # Load and parse the external YAML file for Swagger
    template_file_path = os.path.join(os.getcwd(), 'swagger.yml')
    with open(template_file_path, 'r') as f:
        template = yaml.safe_load(f.read())

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec_1',
                "route": '/apispec_1.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    Swagger(app, template=template, config=swagger_config)

    app.register_blueprint(api_bp, url_prefix='/api')

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
