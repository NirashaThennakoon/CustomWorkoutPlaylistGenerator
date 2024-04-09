"""
    This module responsible for handling functions related to workout plan resource
"""
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import BadRequest
from flask import Response, jsonify, request, url_for, g
from flask_restful import Resource
import requests
from data_models.models import WorkoutPlan, WorkoutPlanItem, Workout
from extensions import db
from extensions import cache
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
import json

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

class WorkoutPlanBuilder(MasonBuilder):
    def add_control_get_workout_plan(self, workout_plan_id):
        self.add_control(
            "custWorkoutPlaylistGen:get-workoutplan",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="GET",
            title="Get Workout Plan by ID"
        )

    def add_control_get_playlist(self, playlist_id):
        self.add_control(
            "custWorkoutPlaylistGen:get-playlist",
            href=f"/api/playlist/{playlist_id}",
            method="GET",
            title="Get Playlist by ID"
        )

    def add_control_get_user(self, user_id):
        self.add_control(
            "custWorkoutPlaylistGen:get-user",
            href=f"/api/user/{user_id}",
            method="GET",
            title="Get User by ID"
        )

    def add_control_add_workout_plan(self):
        self.add_control(
            "custWorkoutPlaylistGen:add-workoutplan",
            href="/api/workoutPlan",
            method="POST",
            title="Add New Workout Plan",
            encoding="json",
            schema=WorkoutPlan.json_schema()  
        )

    def add_control_edit_workout_plan(self, workout_plan_id):
        self.add_control(
            "custWorkoutPlaylistGen:edit-workoutplan",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="PUT",
            title="Edit This Workout Plan",
            encoding="json",
            schema=WorkoutPlan.json_schema()  
        )

    def add_control_delete_workout_plan(self, workout_plan_id):
        self.add_control(
            "custWorkoutPlaylistGen:delete-workoutplan",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="DELETE",
            title="Delete This Workout Plan"
        )

    def add_control_get_workouts(self, workout_plan_id):
        self.add_control(
            "custWorkoutPlaylistGen:get-workoutplanitem",
            href=f"/api/workoutPlanItem/{workout_plan_id}",
            method="GET",
            title="Get Workouts for the Plan"
        )
        
MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
WORKOUT_PLAN_PROFILE = "/profiles/workoutplan/"  
LINK_RELATION = "http://127.0.0.1:5000/api/link-relations/"

def create_error_response(status_code, title, message=None):
    body = WorkoutPlanBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)

class WorkoutPlanResource(Resource):
    """
        This resource includes the workout plan GET, PUT and DELETE endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, workoutPlan):
        """
            This method fetches details about a given workout plan and returns
            them in a list format.

            Args:
                workoutPlan: An object representing the workout plan for which
                information is to be retrieved.

            Returns:
                A tuple containing a list of dictionaries representing workout plan details and
                an HTTP status code. Each dictionary in the list contains keys 'workout_plan_id',
                  'plan_name', 'user_id', and 'duration', populated with corresponding values
                  from the input workout plan object.
        """
        try:
            if not workoutPlan:
                return create_error_response(404, "Workout plan not found")
            
            workout_plan_builder = WorkoutPlanBuilder()
            workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            workout_plan_builder.add_control_add_workout_plan()
            workout_plan_builder.add_control_edit_workout_plan(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control_delete_workout_plan(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control_get_playlist(workoutPlan.playlist_id)
            workout_plan_builder.add_control_get_user(workoutPlan.user_id)
            workout_plan_builder.add_control_get_workouts(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)
            
            workout_plan_dict = {
                "workout_plan_id": workoutPlan.workout_plan_id,
                "plan_name": workoutPlan.plan_name,
                "user_id": workoutPlan.user_id,
                "duration": workoutPlan.duration
            }
            for key, value in workout_plan_dict.items():
                workout_plan_builder[key] = value
            return Response(json.dumps(workout_plan_builder), mimetype=MASON)
        
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))
        
    def put(self, workoutPlan):
        """
            This method updates details about a given workout plan based on the provided data.

            Args:
                workoutPlan: An object representing the workout plan to be updated.

            Returns:
                A dictionary with a message indicating the success of the operation
                and an HTTP status code. The status code indicates the success of the
                operation (200 for successful update).
        """
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")

        data = request.json
        if not data:
            return create_error_response(400, "No input data provided")
        
        if not workoutPlan:
            return create_error_response(404, "Workout plan not found")
        
        try:
            validate(request.json, WorkoutPlan.json_schema(), format_checker=FormatChecker())

            if 'plan_name' in data:
                workoutPlan.plan_name = data['plan_name']
            if 'duration' in data:
                workoutPlan.duration = data['duration']
            if 'user_id' in data:
                workoutPlan.user_id = data['user_id']
            if 'playlist_id' in data:
                workoutPlan.playlist_id = data['playlist_id']

            db.session.commit()
            cache.clear()
            
            workout_plan_builder = WorkoutPlanBuilder()
            workout_plan_builder["message"] = "Workout plan updated successfully"
            
            return Response(json.dumps(workout_plan_builder), 200, mimetype=MASON)
        
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))

    def delete(self, workoutPlan):
        """
            This method deletes details about a given workout plan.

            Args:
                workoutPlan: An object representing the workout plan to be deleted.

            Returns:
                A dictionary with a message indicating the success of the operation
                and an HTTP status code. The status code indicates the success of
                the operation (200 for successful deletion).
        """
        db.session.delete(workoutPlan)
        db.session.commit()
        cache.clear()

        workout_plan_builder = WorkoutPlanBuilder()
        workout_plan_builder["message"] = "Workout plan deleted successfully"
        
        return Response(json.dumps(workout_plan_builder), 200, mimetype=MASON)

class WorkoutPlanCreator(Resource):
    """
        This resource includes the POST workout plan endpoint.
    """
    def post(self):
        """
            This method creates a new workout plan based on the provided data.

            Returns:
                A dictionary with a message indicating the success of the operation,
                the ID of the created workout plan, and an HTTP status code.
                The status code indicates the success of the operation
                (201 for successful creation).
        """
        data = request.json

        if not data or 'workout_ids' not in data:
            return create_error_response(400, "Invalid input data on Create Workout Plan")
        try:
            validate(request.json, WorkoutPlan.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        totalDuration = 0
        
        if not 'plan_name' in data:
            return create_error_response(400, "Plan name not found")
        
        plan_name = data["plan_name"]
        
        if not 'workout_ids' in data:
            return create_error_response(400, "Workout ids not found")
        
        workout_ids = data.get('workout_ids', [])

        data = {
            "playlist_name": f"{plan_name} Playlist",
            "workout_ids": workout_ids
        }
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": g.current_api_key.key
        }

        response = requests.post('http://127.0.0.1:5000/' + url_for('api.playlistcreation'),
                                 json=data, headers=headers)
        playlist_id = response.json()["playlist_id"]
        
        # Create workout plan
        workoutPlan = WorkoutPlan(
            plan_name=plan_name,
            user_id= g.current_api_key.user.id,
            duration=0,
            playlist_id = playlist_id
        )
        db.session.add(workoutPlan)
        db.session.commit()

        for workout_id in workout_ids:
            # calculate total duration of the workout plan
            print(workout_id)
            workout = Workout.query.get(workout_id)
            totalDuration = totalDuration + workout.duration

            # update workout_id and workout_plan_id in WorkoutPlanItem table
            workout_plan_item = WorkoutPlanItem(
                workout_plan_id=workoutPlan.workout_plan_id,
                workout_id=workout_id
            )
            db.session.add(workout_plan_item)
        db.session.commit()

        # update total duration of the workout plan
        workoutPlan = WorkoutPlan.query.get(workoutPlan.workout_plan_id)
        workoutPlan.duration = totalDuration
        db.session.commit()
        cache.clear()

        workout_plan_builder = WorkoutPlanBuilder()
        workout_plan_builder["message"] = "Workout plan created successfully"
        
        return Response(json.dumps(workout_plan_builder), status=201, mimetype=MASON)

class WorkoutPlanItemResource(Resource):
    """
        This resource includes the GET workout plan items endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, workout_plan_id):
        """
            Retrieve information about workout plan items for a given workout plan ID.

            Args:
                workout_plan_id: The ID of the workout plan for which workout plan
                items are to be retrieved.

            Returns:
                A tuple containing a list of dictionaries representing workout plan
                item details and an HTTP status code. Each dictionary in the list
                contains keys 'workout_plan_id' and 'workout_id', populated with
                corresponding values from each workout plan item.
        """
        workoutPlanItem_list = []
        try:
            workoutPlansItem = WorkoutPlanItem.query.filter_by(workout_plan_id=workout_plan_id).all()
            workout_plan_builder = WorkoutPlanBuilder()
            for workoutPlanItem in workoutPlansItem:
                workout_dict = {
                    "workout_plan_id": workoutPlanItem.workout_plan_id,
                    "workout_id": workoutPlanItem.workout_id
                }
                workoutPlanItem_list.append(workout_dict)
                workout_plan_builder["workout list"] = workoutPlanItem_list
            
            return Response(json.dumps(workout_plan_builder), mimetype=MASON)
        except KeyError:
            return create_error_response(400, "Invalid input data")

