"""
   This module responsible for handling functions related to workout resource
"""
from enum import Enum
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import BadRequest
from flask import request, g
from flask_restful import Resource
from data_models.models import Workout
from extensions import db
from extensions import cache

class WorkoutResource(Resource):
    """
        This resource includes the workout GET, PUT and DELETE endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, workout):
        """
            This method fetches details about a given workout and returns them in a list format.

            Args:
                workout: An object representing the workout for which information
                is to be retrieved.

            Returns:
                A tuple containing a list of dictionaries representing workout
                details and an HTTP status code. The status code indicates the
                success of the operation (200 for successful retrieval).
        """
        workout_list = []
        if workout:
            workout_dict = {
                "workout_id": workout.workout_id,
                "workout_name": workout.workout_name,
                "duration": workout.duration,
                "workout_intensity": workout.workout_intensity,
                "equipment": workout.equipment,
                "workout_type": workout.workout_type
            }
            workout_list.append(workout_dict)

        return workout_list, 200

    def put(self, workout):
        """
            This method updates details about a given workout based on the provided data.

            Args:
                workout: An object representing the workout to be updated.

            Returns:
                A dictionary with a message indicating the success of the operation
                and an HTTP status code. The status code indicates the success of
                the operation (200 for successful update).
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400

        try:
            validate(request.json, Workout.json_schema(), format_checker=FormatChecker())

            if 'workout_name' in data:
                workout.workout_name = data['workout_name']
            if 'duration' in data:
                workout.duration = data['duration']
            if 'workout_intensity' in data:
                 # Check if workout_intensity is valid
                intensity = data.get('workout_intensity')
                for e in WorkoutIntensity:
                    if intensity == e.value:
                        workout.workout_intensity = intensity
                        break
                else:
                    return {"message": "Invalid workout intensity"}, 400
            if 'equipment' in data:
                workout.equipment = data['equipment']
            if 'workout_type' in data:
                workout.workout_type = data['workout_type']
            db.session.commit()
            cache.clear()
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e
        except ValueError as e:
            return {"message": "Invalid input data: " + str(e)}, 400

        return {"message": "Workout updated successfully"}, 200

    def delete(self, workout):
        """
            This method deletes details about a given workout if the user has admin privileges.

            Args:
                workout: An object representing the workout to be deleted.

            Returns:
                A dictionary with a message indicating the success of the operation
                and an HTTP status code. The status code indicates the success of the
                operation (200 for successful deletion).
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403

        db.session.delete(workout)
        db.session.commit()
        cache.clear()

        return {"message": "Workout deleted successfully"}, 200

class WorkoutIntensity(Enum):
    """
        An enumeration representing different levels of workout intensities.
    """
    SLOW = "slow"
    MILD = "mild"
    INTERMEDIATE = "intermediate"
    FAST = "fast"
    EXTREME = "extreme"

class WorkoutsCollection(Resource):
    """
        This resource includes the GET all workouts and POST workout endpoint.
    """
    @cache.cached(timeout=60)
    def get(self):
        """
            This method fetches details about all workouts and returns them in a list format.

            Returns:
                A tuple containing a list of dictionaries representing workout
                details and an HTTP status code. The status code indicates the
                success of the operation (200 for successful retrieval).
        """
        workout = Workout.query.all()
        workout_list = []
        for w in workout:  # Iterate over each Workout instance
            workout_dict = {
                "workout_id": w.workout_id,
                "workout_name": w.workout_name,
                "duration": w.duration,
                "workout_intensity": w.workout_intensity,
                "equipment": w.equipment,
                "workout_type": w.workout_type
            }
            workout_list.append(workout_dict)

        return workout_list, 200

    def post(self):
        """
            This method adds a new workout to the database.

            Returns:
                A dictionary with a message indicating the success of the operation
                and an HTTP status code. The status code indicates the success of the
                operation (201 for successful creation).
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403

        data = request.json
        try:
            validate(request.json, Workout.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if (data['duration'] is not None and not isinstance(data['duration'], float)):
            return {"message": "Workout duration must be a float"}, 400
        intensity = data.get('workout_intensity')
        for e in WorkoutIntensity:
            if intensity == e.value:
                workout_intensity = intensity
                break
        else:
            return {"message": "Invalid workout intensity"}, 400
        try:
            workout = Workout(
                workout_name=data["workout_name"],
                duration=data["duration"],
                workout_intensity=workout_intensity,
                equipment=data["equipment"],
                workout_type=data["workout_type"]
            )
            db.session.add(workout)
            db.session.commit()
            cache.clear()
        except ValueError as e:
            return {"message": str(e)}, 400
        return {"message": "Workout added successfully"}, 201
