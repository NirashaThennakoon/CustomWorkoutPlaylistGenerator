"""
   This module responsible for handling functions related to user resource
"""
import datetime
import hashlib
import uuid
from datetime import timedelta
from copy import deepcopy
from flask_jwt_extended import create_access_token
from werkzeug.exceptions import BadRequest
from jsonschema import validate, ValidationError, FormatChecker
from flask import request, g
from flask_restful import Resource
from data_models.models import ApiKey, User
from extensions import db
from extensions import cache

def generate_api_key():
    """
        This function generates a unique API key using UUID version 4.
    """
    return str(uuid.uuid4())

class UserRegistration(Resource):
    """
        This resource includes the user registration POST endpoint.
    """
    def post(self):
        """
            This method registers a new user in the system based on the provided data.

            Returns:
                A tuple containing a dictionary with a message indicating the
                success of the operation, the user ID of the newly registered user,
                and an HTTP status code. If the operation is successful,
                the status code is 201.
        """
        data = request.json
        try:
            validate(request.json, User.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

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

        user = User(email=email, password=hashed_password,
                    height=height, weight=weight, user_type=user_type,
                    user_token=user_token, token_expiration=token_expiration)
        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"error":"Failed to register user"}, 500

        api_key = generate_api_key()
        is_admin = (user_type == 'admin')
        new_api_key = ApiKey(key=api_key, user_id=user.id, admin=is_admin)

        try:
            db.session.add(new_api_key)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"error":"Failed to generate API key"}, 500

        return {"message": "User registered successfully", "user_id": user.id}, 201

# class UserLogin(Resource):
#     """
#         This resource includes the user login POST endpoint.
#     """
#     def post(self):
#         """
#             This method authenticates a user based on the provided email and password.

#             Returns:
#                 A tuple containing a dictionary with a message indicating the
#                 success of the operation, an access token for the authenticated user,
#                 and an HTTP status code. If the operation is successful,
#                 the status code is 200.
#         """
#         data = request.json
#         if not data or not all(key in data for key in ['email', 'password']):
#             return {"message": "Invalid input data for user login"}, 400

#         user_schema = User.json_schema()
#         validate_request(data, user_schema)

#         email = data['email']
#         password = data['password']

#         user = User.query.filter_by(email=email).first()
#         if not user:
#             return {"message": "No such user in the system"}, 404

#         if not user.verify_password(password):
#             return {"message": "Invalid password"}, 401

#         access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
#         return {"message": "Login successful", "access_token": access_token}, 200

class UserResource(Resource):
    """
        This resource includes the GET, DETELE and PUT user endpoints.
    """
    @cache.cached(timeout=60)
    def get(self, user):
        """
        This method fetches details about a given user and returns them in a list format.

        Args:
            user: An object representing the user for which information is to be retrieved.

        Returns:
            A tuple containing a list of dictionaries representing user details
            and an HTTP status code. Each dictionary in the list contains keys
            'email', 'height', 'weight', and 'user_type',
            populated with corresponding values from the input user object.
        """
        user_data = []
        if user:
            song_dict = {
                "email": user.email,
                "height": user.height,
                "weight": user.weight,
                "user_type": user.user_type
            }
        user_data.append(song_dict)
        return user_data, 200

    def delete(self, user):
        """
            This method deletes details about a given user if the user has admin privileges.

            Args:
                user: An object representing the user to be deleted.

            Returns:
                A dictionary with a message indicating the success of the
                operation and an HTTP status code. The status code indicates
                the success of the operation (200 for successful deletion).
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403

        db.session.delete(user)
        db.session.commit()
        return {"message": "User deleted successfully"}, 200

    def put(self, user):
        """
            This method updates details about a given user based on the provided data.

            Args:
                user: An object representing the user to be updated.

            Returns:
                A dictionary with a message indicating the success of the
                operation and an HTTP status code. The status code indicates
                the success of the operation (200 for successful update).
        """
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400

        try:
            validate(request.json, User.json_schema(), format_checker=FormatChecker())

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
            cache.clear()
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e
        except Exception as e:
            return {"message": str(e)}, 400

        return {"message": "User updated successfully"}, 200
    
    def post(self, user):
        """
            This method authenticates a user based on the provided email and password.

            Returns:
                A tuple containing a dictionary with a message indicating the
                success of the operation, an access token for the authenticated user,
                and an HTTP status code. If the operation is successful,
                the status code is 200.
        """
        data = request.json
        if not data or not all(key in data for key in ['email', 'password']):
            return {"message": "Invalid input data for user login"}, 400

        user_schema = User.json_schema()
        validate_request(data, user_schema)

        email = data['email']
        password = data['password']

        user = User.query.filter_by(email=email).first()
        if not user:
            return {"message": "No such user in the system"}, 404

        if not user.verify_password(password):
            return {"message": "Invalid password"}, 401

        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        return {"message": "Login successful", "access_token": access_token}, 200

class ApiKeyResource(Resource):
    """
        This resource includes the API key update endpoint.
    """
    def put(self, user):
        """
            This method generates a new API key and updates it for the given user.

            Args:
                user: An object representing the user for whom the
                API key is to be updated.

            Returns:
                A dictionary with a message indicating the success of the operation,
                the new API key, and an HTTP status code. The status code indicates
                the success of the operation (200 for successful update).
        """
        new_api_key = generate_api_key()
        api_key = ApiKey.query.filter_by(user_id=user.id).first()
        if not api_key:
            return {"message": "API key not found for the user"}, 404

        api_key.key = new_api_key

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return {"message": "Failed to update API key", "error": str(e)}, 500

        return {"message": "API key updated successfully", "new_api_key": new_api_key}, 200

def validate_request(json_data, json_schema):
    """
        This function performs validation of JSON data against a JSON schema
        with specific fields removed. It removes 'height', 'weight', and 'user_type'
          fields from the schema and their corresponding requirements,
          and then validates the JSON data against the modified schema.

        Args:
            json_data: The JSON data to be validated.
            json_schema: The JSON schema against which the data is to be validated.
    """
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
        raise BadRequest(description=str(e)) from e
