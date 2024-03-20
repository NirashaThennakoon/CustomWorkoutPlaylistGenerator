from flask import jsonify, request, g
from flask_restful import Resource
from data_models.models import Workout
from extensions import db
from enum import Enum

class WorkoutResource(Resource):
    def get(self, workout_id):
        try:
            workout = Workout.query.get(workout_id)
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
        except KeyError:
            return jsonify({"message": "Invalid input data"}), 400
        return workout_list, 200

    def put(self, workout_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400

        workout = Workout.query.get(workout_id)
        if not workout:
            return {"message": "Workout not found"}, 404

        try:
            if 'workout_name' in data:
                workout.workout_name = data['workout_name']
            if 'duration' in data:
                workout.duration = data['duration']
            if 'workout_intensity' in data:
                workout.workout_intensity = data['workout_intensity']
            if 'equipment' in data:
                workout.equipment = data['equipment']
            if 'workout_type' in data:
                workout.workout_type = data['workout_type']

            db.session.commit()
        except ValueError as e:
            return {"message": "Invalid input data: " + str(e)}, 400

        return {"message": "Workout updated successfully"}, 200

    def delete(self, workout_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        workout = Workout.query.get(workout_id)
        if not workout:
            return {"message": "Workout not found"}, 404

        db.session.delete(workout)
        db.session.commit()

        return {"message": "Workout deleted successfully"}, 200
    
class WorkoutIntensity(Enum):
    SLOW = "slow"
    MILD = "mild"
    INTERMEDIATE = "intermediate"
    FAST = "fast"
    EXTREME = "extreme"
    
class WorkoutsResource(Resource):
        def get(self):
            try:
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
            except KeyError:
                return jsonify({"message": "Invalid input data"}), 400
            return workout_list, 200
    
        def post(self):
            if g.current_api_key.user.user_type != 'admin':
                return {"message": "Unauthorized access"}, 403
            data = request.json
            if not data or 'workout_name' not in data:
                return {"message": "No workout name provided"}, 400
            
            if (data['duration'] is not None and not isinstance(data['duration'], float)):
                return {"message": "Workout duration must be a float"}, 400

            workout_name = data['workout_name']
            #existing_workout = Workout.query.filter_by(workout_name=workout_name).first()
            # if existing_workout:
            #     return {"error": "workout_name already exists"}, 409
            
            # Check if workout_intensity is valid
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
            except ValueError as e:
                return {"message": str(e)}, 400
            return {"message": "Workout added successfully"}, 201