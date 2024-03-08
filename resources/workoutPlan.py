from flask import jsonify, request, url_for, g
from flask_restful import Resource
import requests
from data_models.models import WorkoutPlan, WorkoutPlanItem, Workout
from extensions import db

class WorkoutPlanResource(Resource):
    def get(self, workout_plan_id):
        workoutPlan_list = []
        try:
            workoutPlan = WorkoutPlan.query.get(workout_plan_id)
            if workoutPlan:
                workout_dict = {
                    "workout_plan_id": workoutPlan.workout_plan_id,
                    "plan_name": workoutPlan.plan_name,
                    "user_id": workoutPlan.user_id,
                    "duration": workoutPlan.duration
                }
                workoutPlan_list.append(workout_dict)
            return jsonify(workoutPlan_list)
        except Exception as e:
            return "500", 500

    def put(self, workout_plan_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400

        workout = WorkoutPlan.query.get(workout_plan_id)
        if not workout:
            return {"message": "Workout plan not found"}, 404

        try:
            if 'plan_name' in data:
                workout.plan_name = data['plan_name']
            if 'duration' in data:
                workout.duration = data['duration']
            if 'user_id' in data:
                workout.user_id = data['user_id']
            if 'playlist_id' in data:
                workout.playlist_id = data['playlist_id']

            db.session.commit()
        except ValueError as e:
            return {"message": str(e)}, 400

        return "", 204

    def delete(self, workout_plan_id):
        workout = WorkoutPlan.query.get(workout_plan_id)
        if not workout:
            return {"message": "Workout plan not found"}, 404

        db.session.delete(workout)
        db.session.commit()

        return "", 204

class WorkoutPlanAddingResource(Resource):
    def post(self):
        data = request.json
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
        print(g.current_api_key.user.id)
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
        
        return "201", 201
    
class WorkoutPlanItemResource(Resource):
    def get(self, workout_plan_id):
        workoutPlanItem_list = []
        try:
            workoutPlansItem = WorkoutPlanItem.query.filter_by(workout_plan_id=workout_plan_id).all()
            for workoutPlanItem in workoutPlansItem:
                workout_dict = {
                    "workout_plan_id": workoutPlanItem.workout_plan_id,
                    "workout_id": workoutPlanItem.workout_id
                }
                workoutPlanItem_list.append(workout_dict)
            return jsonify(workoutPlanItem_list)
        except Exception as e:
            return "500", 500   