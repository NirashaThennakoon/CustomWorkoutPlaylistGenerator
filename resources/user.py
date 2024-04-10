"""
   This module responsible for handling functions related to user resource
"""
import datetime
import hashlib
import uuid
from datetime import timedelta
from copy import deepcopy
from flask_jwt_extended import create_access_token
from jsonschema import validate, ValidationError, FormatChecker
from flask_restful import Resource
from data_models.models import ApiKey, User
from extensions import db
from extensions import cache
from http.client import FORBIDDEN
import json
from flask import Response, jsonify, request, g
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType

def generate_api_key():
    return str(uuid.uuid4())

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

class UserBuilder(MasonBuilder):

    def add_control_edit_user(self, user_id):
        self.add_control(
            "custWorkoutPlaylistGen:edit",
            href=f"/api/users/{user_id}",
            method="PUT",
            title="Edit This User",
            encoding="json",
            schema=User.json_schema()  
        )

    def add_control_delete_user(self, user_id):
        self.add_control(
            "custWorkoutPlaylistGen:delete",
            href=f"/api/user/{user_id}",
            method="DELETE",
            title="Delete This User"
        )

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
USER_PROFILE = "/profiles/user/"  
LINK_RELATION = "/user_link_relation"

def create_error_response(status_code, title, message=None):
    body = UserBuilder()
    body.add_error(title, message if message else "")
    body.add_namespace("user", USER_PROFILE)
    return Response(json.dumps(body), status_code, mimetype=MASON)

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
            return create_error_response(400, "Invalid JSON document", str(e))

        email = data['email']
        password = data['password']
        height = data['height']
        weight = data['weight']
        user_type = data['user_type']

        if User.query.filter_by(email=email).first():
            return create_error_response(400, "Email already exists")

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
            return create_error_response(500, "Failed to register user", str(e))

        api_key = generate_api_key()
        is_admin = (user_type == 'admin')
        new_api_key = ApiKey(key=api_key, user_id=user.id, admin=is_admin)

        try:
            db.session.add(new_api_key)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return create_error_response(500, "Failed to generate API key", str(e))

        response_builder = UserBuilder()
        response_builder["message"] = "User registered successfully"
        response_builder["user_id"] = user.id

        return Response(json.dumps(response_builder), 201, mimetype=MASON)

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
        if not user:
            return create_error_response(404, "User not found")
        
        user_builder = UserBuilder()
        user_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
        user_builder.add_control_edit_user(user.id)
        user_builder.add_control_delete_user(user.id)
        user_builder.add_control("profile", href=USER_PROFILE)
        
        user_data = {
            "email": user.email,
            "height": user.height,
            "weight": user.weight,
            "user_type": user.user_type
        }
        for key, value in user_data.items():
            user_builder[key] = value

        return Response(json.dumps(user_builder), mimetype=MASON)

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
            return create_error_response(403, "Unauthorized access")

        db.session.delete(user)
        db.session.commit()
        
        user_builder = UserBuilder()
        user_builder["message"] = "User deleted successfully"

        return Response(json.dumps(user_builder), mimetype=MASON)

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
            return create_error_response(400, "No input data provided")

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
                return create_error_response(400, "Invalid JSON document", str(e))
        except Exception as e:
            db.session.rollback()
            return create_error_response(500, "Internal Server Error", str(e))
        
        user_builder = UserBuilder()
        user_builder["message"] = "User updated successfully"
        
        return Response(json.dumps(user_builder), mimetype=MASON)
    
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
            return create_error_response(400, "Invalid input data for user login")

        user_schema = User.json_schema()
        validate_request(data, user_schema)

        email = data['email']
        password = data['password']

        user = User.query.filter_by(email=email).first()
        if not user:
            return create_error_response(404, "No such user in the system")

        if not user.verify_password(password):
            return create_error_response(401, "Invalid password")

        access_token = create_access_token(identity=user.id, expires_delta=timedelta(days=1))
        
        user_builder = UserBuilder()
        user_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION) 
        user_builder.add_control_edit_user(user.id)
        user_builder.add_control_delete_user(user.id)
        user_builder.add_control("profile", href=USER_PROFILE)
        user_builder["message"] = "Login successful"
        user_builder["access_token"] = access_token

        return Response(json.dumps(user_builder), status=200, mimetype=MASON)

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
            return create_error_response(404, "API key not found for the user")

        api_key.key = new_api_key

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            return create_error_response(500, "Failed to update API key", str(e))

        api_key_builder = MasonBuilder()
        api_key_builder.add_namespace("apikey", "/profiles/apikey/")
        api_key_builder["message"] = "API key updated successfully"
        api_key_builder["new_api_key"] = new_api_key
        api_key_builder.add_control("self", href=f"/api/users/update_api_key/{user.id}", title="API Key")

        return Response(json.dumps(api_key_builder), status=200, mimetype=MASON)

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
