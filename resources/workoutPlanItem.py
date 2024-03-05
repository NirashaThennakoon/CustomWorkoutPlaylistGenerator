from extensions import db
from flask import jsonify, request
from flask_restful import Resource
from models import WorkoutPlanItem

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