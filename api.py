from flask import Blueprint, render_template
from flask_restful import Api
from resources.workout import WorkoutResource,WorkoutsCollection
from resources.workoutPlan import WorkoutPlanResource, WorkoutPlanCreator, WorkoutPlanItemResource
from resources.song import SongResource, SongsCollection
from resources.playlist import PlaylistResource, PlaylistCreation, PlaylistItemResource
from resources.user import UserRegistration, UserResource, ApiKeyResource

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
api.add_resource(PlaylistItemResource, "/playlistItem/<playlist_id>")
api.add_resource(UserRegistration, "/user")
api.add_resource(UserResource, "/user/<user:user>")
api.add_resource(ApiKeyResource, "/user/update_api_key/<user:user>")

@api_bp.route('/link_relation')
def link_page():
    return render_template('link_relation.html')