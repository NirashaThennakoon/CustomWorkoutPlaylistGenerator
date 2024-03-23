from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from data_models.models import Workout, Playlist, Song, WorkoutPlan, WorkoutPlanItem, PlaylistItem, User, ApiKey

class WorkoutConverter(BaseConverter):
    
    def to_python(self, workout_id):
        workout = Workout.query.get(workout_id)
        if workout is None:
            raise NotFound(f"Workout with id :{workout_id} not found.")
        return workout
        
    def to_url(self, workout):
        return str(workout.workout_id)
    
class SongConverter(BaseConverter):
    
    def to_python(self, song_id):
        song = Song.query.get(song_id)
        if song is None:
            raise NotFound(f"Song with id :{song_id} not found.")
        return song
        
    def to_url(self, song):
        return str(song.song_id)
    
class WorkoutPlanConverter(BaseConverter):
    
    def to_python(self, workout_plan_id):
        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if workout_plan is None:
            raise NotFound(f"Workout Plan with id :{workout_plan_id} not found.")
        return workout_plan
        
    def to_url(self, workout_plan):
        return str(workout_plan.workout_plan_id)
    
class PlaylistConverter(BaseConverter):
    
    def to_python(self, playlist_id):
        playlist = Playlist.query.get(playlist_id)
        if playlist is None:
            raise NotFound(f"Playlist with id :{playlist_id} not found.")
        return playlist
        
    def to_url(self, playlist):
        return str(playlist.playlist_id)
    
class UserConverter(BaseConverter):
    
    def to_python(self, user_id):
        user = User.query.get(user_id)
        if user is None:
            raise NotFound(f"User with id :{user_id} not found.")
        return user
        
    def to_url(self, user):
        return str(user.id)