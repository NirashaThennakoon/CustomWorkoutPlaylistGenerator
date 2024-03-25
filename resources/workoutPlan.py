"""
    This module responsible for handling functions related to workout plan resource
"""
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import BadRequest
from flask import jsonify, request, url_for, g
from flask_restful import Resource
import requests
from data_models.models import WorkoutPlan, WorkoutPlanItem, Workout
from extensions import db
from extensions import cache

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
        workoutPlan_list = []
        if workoutPlan:
            workout_dict = {
                "workout_plan_id": workoutPlan.workout_plan_id,
                "plan_name": workoutPlan.plan_name,
                "user_id": workoutPlan.user_id,
                "duration": workoutPlan.duration
            }
            workoutPlan_list.append(workout_dict)

        return workoutPlan_list, 200

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
            return {"message": "Unauthorized access"}, 403

        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400
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
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e
        except ValueError as e:
            return {"message": str(e)}, 400

        return {"message": "Workout plan updated successfully"}, 200

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

        return {"message": "Workout plan deleted successfully"}, 200

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
            return {"message": "Invalid input data on Create Workout Plan"}, 400

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

        return {"message": "Workout plan created successfully",
                "workout_plan_id": workoutPlan.workout_plan_id}, 201

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
            for workoutPlanItem in workoutPlansItem:
                workout_dict = {
                    "workout_plan_id": workoutPlanItem.workout_plan_id,
                    "workout_id": workoutPlanItem.workout_id
                }
                workoutPlanItem_list.append(workout_dict)
        except KeyError:
            return jsonify({"message": "Invalid input data"}), 400
        return workoutPlanItem_list, 200

