"""
    This module responsible for handling functions related to workout plan resource
"""
import json
from jsonschema import validate, ValidationError, FormatChecker
from flask import Response, request, url_for, g
from flask_restful import Resource
import requests
from werkzeug.exceptions import BadRequest, NotFound
from data_models.models import WorkoutPlan, WorkoutPlanItem, Workout
from extensions import db, cache

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
    """
        A class for building workout plan-related MASON hypermedia representations.
    """
    def add_control_get_playlist(self, playlist_id):
        """
            Adds a control to get a playlist by its ID.
        """
        self.add_control(
            "custWorkoutPlaylistGen:playlist",
            href=f"/api/playlist/{playlist_id}",
            method="GET",
            title="Get Playlist by ID"
        )

    def add_control_get_user(self, user_id):
        """
            Adds a control to get a user by its ID.
        """
        self.add_control(
            "author",
            href=f"/api/user/{user_id}",
            method="GET",
            title="Get User by ID"
        )

    def add_control_edit_workout_plan(self, workout_plan_id):
        """
            Adds a control to edit a workout plan.
        """
        self.add_control(
            "edit",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="PUT",
            title="Edit This Workout Plan",
            encoding="json",
            schema=WorkoutPlan.json_schema()
        )
    
    def add_control_get_workout_plan(self, workout_plan_id):
        """
            Adds a control to get a workout plan by its ID.
        """
        self.add_control(
            "item",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="GET",
            title="Get Workout plan by workout_plan_id"
        )

    def add_control_delete_workout_plan(self, workout_plan_id):
        """
            Adds a control to delete a workout plan.
        """
        self.add_control(
            "delete",
            href=f"/api/workoutPlan/{workout_plan_id}",
            method="DELETE",
            title="Delete This Workout Plan"
        )

    def add_control_get_workouts(self, workout_plan_id):
        """
            Adds a control to get workouts for a workout plan.
        """
        self.add_control(
            "item",
            href=f"/api/workoutPlanItem/{workout_plan_id}",
            method="GET",
            title="Get Workouts for the Plan"
        )

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
WORKOUT_PLAN_PROFILE = "/profile"  
LINK_RELATION = "/workout_plan_link_relation"

def create_error_response(status_code, title, message=None):
    """
        Creates an error response with a MASON hypermedia representation for workout plans.
    """
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

            workout_plan_builder = WorkoutPlanBuilder()
            workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            workout_plan_builder.add_control_edit_workout_plan(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control_delete_workout_plan(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control_get_playlist(workoutPlan.playlist_id)
            workout_plan_builder.add_control_get_user(workoutPlan.user_id)
            workout_plan_builder.add_control_get_workouts(workoutPlan.workout_plan_id)
            workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)

            workoutplan_items = WorkoutPlanItem.query.filter_by(workout_plan_id=workoutPlan.workout_plan_id).all()

            workouts_list = []
            for item in workoutplan_items:
                workout = Workout.query.get(item.workout_id)
                if workout:
                    workout_dict = {
                        "workout_id": workout.workout_id,
                        "workout_name": workout.workout_name,
                        "duration": workout.duration,
                        "workout_intensity": workout.workout_intensity,
                        "equipment": workout.equipment,
                        "workout_type": workout.workout_type,
                    }
                workouts_list.append(workout_dict)

            workout_plan_dict = {
                "workout_plan_id": workoutPlan.workout_plan_id,
                "plan_name": workoutPlan.plan_name,
                "user_id": workoutPlan.user_id,
                "playlist_id": workoutPlan.playlist_id,
                "duration": workoutPlan.duration,
                "workouts_list": workouts_list
            }
            for key, value in workout_plan_dict.items():
                workout_plan_builder[key] = value
            return Response(json.dumps(workout_plan_builder), mimetype=MASON)

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
            workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)
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
        workoutplan_items = WorkoutPlanItem.query.filter_by(workout_plan_id=workoutPlan.workout_plan_id).all()

        # Delete workoutplan items
        for item in workoutplan_items:
            db.session.delete(item)

        db.session.delete(workoutPlan)
        db.session.commit()
        cache.clear()

        workout_plan_builder = WorkoutPlanBuilder()
        workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
        workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)
        workout_plan_builder["message"] = "Workout plan deleted successfully"

        return Response(json.dumps(workout_plan_builder), 200, mimetype=MASON)

class WorkoutPlanByUserResource(Resource):
    """
        This resource includes the user workout plan GET endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, user):
        """
            This method fetches details about a workout plan belongs to given user and returns
            them in a list format.

            Args:
                userid: An id representing the workout plan for which
                information is to be retrieved.

            Returns:
                A tuple containing a list of dictionaries representing workout plan details and
                an HTTP status code. Each dictionary in the list contains keys 'workout_plan_id',
                  'plan_name', 'user_id', and 'duration', populated with corresponding values
                  from the input workout plan object.
        """
        try:
            workoutPlans = WorkoutPlan.query.filter_by(user_id=user.id).all()
            if workoutPlans is None:
                raise NotFound(f"Workout Plan for the user with id :{user} not found.")
            workout_plans_builder = WorkoutPlanBuilder()
            workout_plans_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            workout_plans_list = []
            for workoutPlan in workoutPlans:
                
                workout_plan_builder = WorkoutPlanBuilder()
                workout_plan_builder.add_control_get_workout_plan(workoutPlan.workout_plan_id)
                # workout_plan_builder.add_control_delete_workout_plan(workoutPlan.workout_plan_id)
                # workout_plan_builder.add_control_get_playlist(workoutPlan.playlist_id)
                # workout_plan_builder.add_control_get_user(workoutPlan.user_id)
                # workout_plan_builder.add_control_get_workouts(workoutPlan.workout_plan_id)
                # workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)

                workoutplan_items = WorkoutPlanItem.query.filter_by(workout_plan_id=workoutPlan.workout_plan_id).all()

                workouts_list = []
                for item in workoutplan_items:
                    workout = Workout.query.get(item.workout_id)
                    if workout:
                        workout_dict = {
                            "workout_id": workout.workout_id,
                            "workout_name": workout.workout_name,
                            "duration": workout.duration,
                            "workout_intensity": workout.workout_intensity,
                            "equipment": workout.equipment,
                            "workout_type": workout.workout_type
                        }
                    workouts_list.append(workout_dict)
                    print(workouts_list)
                workout_plan_dict = {
                    "workout_plan_id": workoutPlan.workout_plan_id,
                    "plan_name": workoutPlan.plan_name,
                    "user_id": workoutPlan.user_id,
                    "playlist_id": workoutPlan.playlist_id,
                    "duration": workoutPlan.duration,
                    "workouts_list": workouts_list
                }
                for key, value in workout_plan_dict.items():
                    workout_plan_builder[key] = value
                workout_plans_list.append(workout_plan_builder)
                
            workout_plans_builder["workout_plans_list"] = workout_plans_list   
            return Response(json.dumps(workout_plans_builder), mimetype=MASON)
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))

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

        plan_name = data["plan_name"]

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
        workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
        workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)
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
            workoutPlansItem = WorkoutPlanItem.query.filter_by(
                workout_plan_id=workout_plan_id).all()
            workout_plan_builder = WorkoutPlanBuilder()
            for workoutPlanItem in workoutPlansItem:
                workout_dict = {
                    "workout_plan_id": workoutPlanItem.workout_plan_id,
                    "workout_id": workoutPlanItem.workout_id
                }
                workoutPlanItem_list.append(workout_dict)
                workout_plan_builder["workout list"] = workoutPlanItem_list
                workout_plan_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
                workout_plan_builder.add_control("profile", href=WORKOUT_PLAN_PROFILE)

            return Response(json.dumps(workout_plan_builder), mimetype=MASON)
        except KeyError:
            return create_error_response(400, "Invalid input data")
