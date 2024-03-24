from flask import Response, jsonify, request, url_for, g
from flask_restful import Resource
import requests
from data_models.models import WorkoutPlan, WorkoutPlanItem, Workout
from extensions import db
from extensions import cache
from jsonschema import validate, ValidationError, FormatChecker
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
            "workoutplan:get",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="GET",
            title="Get Workout Plan by ID"
        )

    def add_control_add_workout_plan(self):
        self.add_control(
            "workoutplan:add",
            href="/api/workoutPlan",
            method="POST",
            title="Add New Workout Plan",
            encoding="json",
            schema=WorkoutPlan.json_schema()  
        )

    def add_control_edit_workout_plan(self, workout_plan_id):
        self.add_control(
            "workoutplan:edit",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="PUT",
            title="Edit This Workout Plan",
            encoding="json",
            schema=WorkoutPlan.json_schema()  
        )

    def add_control_delete_workout_plan(self, workout_plan_id):
        self.add_control(
            "workoutplan:delete",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="DELETE",
            title="Delete This Workout Plan"
        )

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
WORKOUT_PLAN_PROFILE = "/profiles/workoutplan/"  


def create_error_response(status_code, title, message=None):
    body = WorkoutPlanBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)

class WorkoutPlanResource(Resource):
    @cache.cached(timeout=60)
    def get(self, workout_plan_id):
        try:
            workout_plan = WorkoutPlan.query.get(workout_plan_id)
            if not workout_plan:
                return create_error_response(404, "Workout plan not found")
            
            workout_plan_builder = WorkoutPlanBuilder()
            workout_plan_builder.add_namespace("workoutplan", WORKOUT_PLAN_PROFILE)
            workout_plan_builder.add_control_get_workout_plan(workout_plan_id)
            workout_plan_builder.add_control_edit_workout_plan(workout_plan_id)
            workout_plan_builder.add_control_delete_workout_plan(workout_plan_id)
            workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)

            workout_plan_dict = {
                "workout_plan_id": workout_plan.workout_plan_id,
                "plan_name": workout_plan.plan_name,
                "user_id": workout_plan.user_id,
                "duration": workout_plan.duration
            }
            workout_plan_builder.update(workout_plan_dict)

            return Response(json.dumps(workout_plan_builder), mimetype=MASON)
        except KeyError:
            return create_error_response(400, "Invalid input data")

    def put(self, workout_plan_id):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")

        data = request.json
        if not data:
            return create_error_response(400, "No input data provided")

        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if not workout_plan:
            return create_error_response(404, "Workout plan not found")

        try:
            validate(data, WorkoutPlan.json_schema(), format_checker=FormatChecker())

            workout_plan.plan_name = data.get('plan_name', workout_plan.plan_name)
            workout_plan.duration = data.get('duration', workout_plan.duration)
            workout_plan.user_id = data.get('user_id', workout_plan.user_id)

            db.session.commit()
            cache.clear()
            
            workout_plan_builder = WorkoutPlanBuilder()
            workout_plan_builder.add_namespace("workoutplan", WORKOUT_PLAN_PROFILE)
            workout_plan_builder.add_control_get_workout_plan(workout_plan_id)
            workout_plan_builder.add_control_edit_workout_plan(workout_plan_id)
            workout_plan_builder.add_control_delete_workout_plan(workout_plan_id)
            workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)
            workout_plan_builder["message"] = "Workout plan updated successfully"

            return Response(json.dumps(workout_plan_builder), 200, mimetype=MASON)
        
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

    def delete(self, workout_plan_id):
        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if not workout_plan:
            return create_error_response(404, "Workout plan not found")

        db.session.delete(workout_plan)
        db.session.commit()
        cache.clear()
        
        workout_plan_builder = WorkoutPlanBuilder()
        workout_plan_builder["message"] = "Workout plan deleted successfully"
        
        workout_plan_builder.add_control_get_workout_plan(workout_plan_id)
        
        return Response(json.dumps(workout_plan_builder), 200, mimetype=MASON)

class WorkoutPlanAddingResource(Resource):
    def post(self):
        data = request.json
        
        if not data or 'workout_ids' not in data:
            return create_error_response(400, "Invalid input data on Create Workout Plan")
        
        try:
            validate(request.json, WorkoutPlan.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
                raise BadRequest(description=str(e))
        totalDuration = 0
        data = request.json
        
        if not data:
            return create_error_response(400, "No input data provided") 
        
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

        response = requests.post('http://127.0.0.1:5000/' + url_for('api.createplaylistresource'), json=data, headers=headers)
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
        workout_plan_builder.add_control_get_workout_plan(workoutPlan.workout_plan_id)
        workout_plan_builder["message"] = "Workout plan created successfully"
        
        return Response(json.dumps(workout_plan_builder), status=201, mimetype=MASON)
