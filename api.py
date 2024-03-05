from flask import Blueprint
from flask_restful import Api
from resources.workout import WorkoutResource,WorkoutsResource
from resources.workoutPlan import WorkoutPlanResource, WorkoutPlanAddingResource
from resources.workoutPlanItem import WorkoutPlanItemResource

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

api.add_resource(WorkoutResource, "/workout/<workout_id>")
api.add_resource(WorkoutsResource, "/workout")
api.add_resource(WorkoutPlanResource, "/workoutPlan/<workout_plan_id>")
api.add_resource(WorkoutPlanAddingResource, "/workoutPlan")
api.add_resource(WorkoutPlanItemResource, "/workoutPlanItem/<workout_plan_id>")
