from flask import Response, jsonify, request, g
from flask_restful import Resource
from data_models.models import Workout
from extensions import db
from extensions import cache
from enum import Enum
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

class WorkoutBuilder(MasonBuilder):
    def add_control_all_workouts(self):
        self.add_control(
            "workout:all",
            href="/api/workout",
            method="GET",
            title="List All Workouts"
        )
        
    def add_control_get_workout(self, workout_id):
        self.add_control(
            "workout:get",
            href=f"/api/workout/{workout_id}",
            method="GET",
            title="Get Workout by workout_id"
        )

    def add_control_add_workout(self):
        self.add_control(
            "workout:add",
            href="/api/workout",
            method="POST",
            title="Add New Workout",
            encoding="json",
            schema=Workout.json_schema()
        )

    def add_control_edit_workout(self, workout_id):
        self.add_control(
            "workout:edit",
            href=f"/api/workout/{workout_id}",
            method="PUT",
            title="Edit This Workout",
            encoding="json",
            schema=Workout.json_schema()
        )

    def add_control_delete_workout(self, workout_id):
        self.add_control(
            "workout:delete",
            href=f"/api/workout/{workout_id}",
            method="DELETE",
            title="Delete This Workout"
        )

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
WORKOUT_PROFILE = "/profiles/workout/"  

def create_error_response(status_code, title, message=None):
    body = WorkoutBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)
      
class WorkoutResource(Resource):
    @cache.cached(timeout=60)
    def get(self, workout_id):
        workout = Workout.query.get(workout_id)
        if not workout:
            return create_error_response(400, "Invalid input data")

        workout_builder = WorkoutBuilder()
        workout_builder.add_namespace("workout", WORKOUT_PROFILE)
        workout_builder.add_control_get_workout(workout_id)
        workout_builder.add_control_edit_workout(workout_id)
        workout_builder.add_control_delete_workout(workout_id)
        workout_builder.add_control("profile", href=WORKOUT_PROFILE)

        workout_dict = {
            "workout_id": workout.workout_id,
            "workout_name": workout.workout_name,
            "duration": workout.duration,
            "workout_intensity": workout.workout_intensity,
            "equipment": workout.equipment,
            "workout_type": workout.workout_type
        }
        for key, value in workout_dict.items():
            workout_builder[key] = value
        return Response(json.dumps(workout_builder), mimetype=MASON)

    def put(self, workout_id):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")

        data = request.json
        if not data:
            return create_error_response(400, "No input data provided")

        workout = Workout.query.get(workout_id)
        if not workout:
            return create_error_response(404, "Workout not found")

        try:
            validate(data, Workout.json_schema(), format_checker=FormatChecker())

            # Updating workout details
            workout.workout_name = data.get('workout_name', workout.workout_name)
            workout.duration = data.get('duration', workout.duration)
            workout.workout_intensity = data.get('workout_intensity', workout.workout_intensity)
            workout.equipment = data.get('equipment', workout.equipment)
            workout.workout_type = data.get('workout_type', workout.workout_type)

            db.session.commit()
            cache.clear()

            # Creating a response with hypermedia controls to indicate successful update
            workout_builder = WorkoutBuilder()
            workout_builder.add_namespace("workout", WORKOUT_PROFILE)
            workout_builder.add_control_get_workout(workout_id)
            workout_builder.add_control_edit_workout(workout_id)
            workout_builder.add_control_delete_workout(workout_id)
            workout_builder.add_control("profile", href=WORKOUT_PROFILE)
            workout_builder["message"] = "Workout updated successfully"

            return Response(json.dumps(workout_builder), 200, mimetype=MASON)

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))

    def delete(self, workout_id):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")

        workout = Workout.query.get(workout_id)
        if not workout:
            return create_error_response(404, "Workout not found")

        db.session.delete(workout)
        db.session.commit()
        cache.clear()

        workout_builder = WorkoutBuilder()
        workout_builder["message"] = "Workout deleted successfully"
        
        workout_builder.add_control_all_workouts()

        return Response(json.dumps(workout_builder), 200, mimetype=MASON)
    
class WorkoutIntensity(Enum):
    SLOW = "slow"
    MILD = "mild"
    INTERMEDIATE = "intermediate"
    FAST = "fast"
    EXTREME = "extreme"
    
class WorkoutsResource(Resource):
        @cache.cached(timeout=60)
        def get(self):
            workout_builder = WorkoutBuilder()
            workout_builder.add_namespace("workout", WORKOUT_PROFILE)
            workout_builder.add_control_add_workout()  
            try:
                workouts = Workout.query.all()
                items = []
                for w in workouts:
                    workout_item = WorkoutBuilder()
                    workout_id = w.workout_id
                    workout_item.add_control_get_workout(workout_id)
                    workout_item.add_control_edit_workout(workout_id)
                    workout_item.add_control_delete_workout(workout_id)
                    workout_item.add_control("profile", href=WORKOUT_PROFILE)
                    
                    workout_item.update({
                        "workout_id": workout_id,
                        "workout_name": w.workout_name,
                        "duration": w.duration,
                        "workout_intensity": w.workout_intensity,
                        "equipment": w.equipment,
                        "workout_type": w.workout_type
                    })

                    items.append(workout_item)

                workout_builder["items"] = items
                workout_builder.add_control("self", href="/api/workout/", title="Self")

                return Response(json.dumps(workout_builder), 200, mimetype=MASON)

            except Exception as e:
                return create_error_response(400, "Invalid input data", str(e))
    
        def post(self):
            if g.current_api_key.user.user_type != 'admin':
                return create_error_response(403, "Unauthorized access")

            data = request.json

            try:
                validate(data, Workout.json_schema(), format_checker=FormatChecker())
            except ValidationError as e:
                return create_error_response(400, "Invalid JSON document", str(e))

            if 'duration' in data and not isinstance(data['duration'], (float, int)):  
                return create_error_response(400, "Workout duration must be a number")
            
            if 'workout_intensity' in data and data['workout_intensity'] not in [e.value for e in WorkoutIntensity]:
                return create_error_response(400, "Invalid workout intensity")

            try:
                workout = Workout(
                    workout_name=data["workout_name"],
                    duration=data["duration"],
                    workout_intensity=data["workout_intensity"],
                    equipment=data["equipment"],
                    workout_type=data["workout_type"]
                )
                db.session.add(workout)
                db.session.commit()
                cache.clear()

                response_builder = WorkoutBuilder()
                response_builder.add_control_get_workout(workout.workout_id)
                response_builder["message"] = "Workout added successfully"

                return Response(json.dumps(response_builder), status=201, mimetype=MASON)
            except Exception as e: 
                return create_error_response(500, "Internal Server Error", str(e))