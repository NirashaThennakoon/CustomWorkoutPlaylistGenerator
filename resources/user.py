import datetime
import hashlib
from http.client import FORBIDDEN
from flask import jsonify, request, g
from flask_restful import Resource
from data_models.models import ApiKey, User
from extensions import db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from copy import deepcopy
import uuid

def generate_api_key():
    return str(uuid.uuid4())

class UserRegistrationResource(Resource):
    def post(self):
        data = request.json
        if not data or not all(key in data for key in ['email', 'password', 'height', 'weight', 'user_type']):
            return {"message": "Invalid input data for user registration"}, 400
        
        try:         
            validate(request.json, User.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
                raise BadRequest(description=str(e))
        
        email = data['email']
        password = data['password']
        height = data['height']
        weight = data['weight']
        user_type = data['user_type']
        
        if User.query.filter_by(email=email).first():
            return {"message": "Email already exists"}, 400
        
        hashed_password = User.password_hash(password)
        user_token = hashlib.sha256(email.encode()).hexdigest()
        token_expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)

        user = User(email=email, password=hashed_password, height=height, weight=weight, user_type=user_type,
                    user_token=user_token, token_expiration=token_expiration)
        
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"Failed to register user"}, 500
        
       
        api_key = generate_api_key()
        is_admin = (user_type == 'admin')
        new_api_key = ApiKey(key=api_key, user_id=user.id, admin=is_admin)
        
        try:
            db.session.add(new_api_key)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"Failed to generate API key"}, 500
        
        return {"message": "User registered successfully", "user_id": user.id}, 201

class UserLoginResource(Resource):
    def post(self):
        data = request.json
        if not data or not all(key in data for key in ['email', 'password']):
            return {"message": "Invalid input data for user login"}, 400
        
        user_schema = User.json_schema()
        validate_request(data, user_schema)
        
        email = data['email']
        password = data['password']

        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "No sucxh user in the system"}, 404
        
        if not user.verify_password(password):
            return {"message": "Invalid password"}, 401
        
        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        return {"message": "Login successful", "access_token": access_token}, 200

class UserResource(Resource):
    def delete(self, user_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404

        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted successfully"}, 200

    def put(self, user_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400
        
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        try:
            if 'email' in data:
                user.email = data['email']
            if 'password' in data:
                user.password = User.password_hash(data['password'])
            if 'height' in data:
                user.height = data['height']
            if 'weight' in data:
                user.weight = data['weight']
            if 'user_type' in data:
                user.user_type = data['user_type']
            
            db.session.commit()
        except Exception as e:
            return {"message": str(e)}, 400
        
        return {"message": "User updated successfully"}, 200
    
class ApiKeyUpdateResource(Resource):
    def put(self, user_id):
        user = User.query.get(user_id)
        if not user:
            return {"message": "User not found"}, 404
        
        new_api_key = generate_api_key()
        api_key = ApiKey.query.filter_by(user_id=user_id).first()
        if not api_key:
            return {"message": "API key not found for the user"}, 404

        api_key.key = new_api_key

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "Failed to update API key", "error": str(e)}, 500
        
        return {"message": "API key updated successfully", "new_api_key": new_api_key}, 200

    #valdiate login request using same User model schema 
def validate_request(json_data, json_schema):
    json_schema_copy = deepcopy(json_schema)
    if 'height' in json_schema_copy['properties']:
        del json_schema_copy['properties']['height']
    if 'weight' in json_schema_copy['properties']:
        del json_schema_copy['properties']['weight']
    if 'user_type' in json_schema_copy['properties']:
        del json_schema_copy['properties']['user_type']

    if 'required' in json_schema_copy:
        for item in ['height', 'weight', 'user_type']:
            if item in json_schema_copy['required']:
                json_schema_copy['required'].remove(item)

    try:
        validate(json_data, json_schema_copy, format_checker=FormatChecker())
    except ValidationError as e:
        raise BadRequest(description=str(e))
