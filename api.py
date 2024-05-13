"""
   This module responsible for all resources and route mapping
"""
from flask import Blueprint
from flask_restful import Api
from resources.workout import WorkoutResource,WorkoutsCollection, WorkoutItemResource
from resources.workoutPlan import WorkoutPlanByUserResource, WorkoutPlanResource, WorkoutPlanCreator, WorkoutPlanItemResource
from resources.song import SongResource, SongsCollection, AllSongsResource
from resources.playlist import PlaylistResource, PlaylistCreation, PlaylistItemResource
from resources.user import UserRegistration, UserResource, ApiKeyResource, UserLogin

api_bp = Blueprint('api', __name__)
api = Api(api_bp)

api.add_resource(WorkoutResource, "/workout/<workout:workout>", endpoint='workoutresource')
api.add_resource(WorkoutsCollection, "/workout")
api.add_resource(WorkoutItemResource, "/workoutItem/<workout_id>")
api.add_resource(WorkoutPlanResource, "/workoutPlan/<workoutPlan:workoutPlan>", endpoint='workoutplanresource')
api.add_resource(WorkoutPlanByUserResource, "/<user:user>/workoutPlan")
api.add_resource(WorkoutPlanCreator, "/workoutPlan")
api.add_resource(WorkoutPlanItemResource, "/workoutPlanItem/<workout_plan_id>")
api.add_resource(SongResource, "/song/<song:song>/", endpoint='songresource')
api.add_resource(SongsCollection, "/song/")
api.add_resource(AllSongsResource, "/allSong/<song_id>")
api.add_resource(PlaylistResource, "/playlist/<playlist:playlist>/", endpoint='playlistresource')
api.add_resource(PlaylistCreation, "/playlist/")
api.add_resource(PlaylistItemResource, "/playlistItem/<playlist_id>")
api.add_resource(UserRegistration, "/user")
api.add_resource(UserResource, "/user/<user:user>", endpoint='userresource')
api.add_resource(UserLogin, "/user/<string:email>/")
api.add_resource(ApiKeyResource, "/user/update_api_key/<user:user>")
