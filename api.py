from flask import Blueprint
from flask_restful import Api
from resources.workout import WorkoutResource,WorkoutsCollection
from resources.workoutPlan import WorkoutPlanResource, WorkoutPlanCreator, WorkoutPlanItemResource
from resources.song import SongResource
from resources.song import SongsCollection
from resources.playlist import PlaylistResource
from resources.playlist import PlaylistCreation
from resources.user import UserRegistration, UserLogin, UserResource, ApiKeyResource

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

api.add_resource(WorkoutResource, "/workout/<workout:workout>")
api.add_resource(WorkoutsCollection, "/workout")
api.add_resource(WorkoutPlanResource, "/workoutPlan/<workoutPlan:workoutPlan>")
api.add_resource(WorkoutPlanCreator, "/workoutPlan")
api.add_resource(WorkoutPlanItemResource, "/workoutPlanItem/<workout_plan_id>")
api.add_resource(SongResource, "/song/<song:song>/")
api.add_resource(SongsCollection, "/song/")
api.add_resource(PlaylistResource, "/playlist/<playlist:playlist>/")
api.add_resource(PlaylistCreation, "/playlist/")
api.add_resource(UserRegistration, "/user/register")
api.add_resource(UserLogin, "/user/login")
api.add_resource(UserResource, "/user/<user:user>")
api.add_resource(ApiKeyResource, "/user/update_api_key/<user:user>")
