"""
   This module responsible for converting incoming IDs in requests to objects
"""
from werkzeug.exceptions import NotFound
from werkzeug.routing import BaseConverter
from data_models.models import Workout, Playlist, Song, WorkoutPlan, User

class WorkoutConverter(BaseConverter):
    """
    Converter for mapping workout IDs to Workout objects and vice versa.
    """

    def to_python(self, workout_id):
        """
        Convert workout ID to Workout object.
        """
        workout = Workout.query.get(workout_id)
        if workout is None:
            raise NotFound(f"Workout with id :{workout_id} not found.")
        return workout

class SongConverter(BaseConverter):
    """
    Converter for mapping song IDs to Song objects and vice versa.
    """

    def to_python(self, song_id):
        """
        Convert song ID to song object.
        """
        song = Song.query.get(song_id)
        if song is None:
            raise NotFound(f"Song with id :{song_id} not found.")
        return song

class WorkoutPlanConverter(BaseConverter):
    """
    Converter for mapping workout plan IDs to WorkoutPlan objects and vice versa.
    """

    def to_python(self, workout_plan_id):
        """
        Convert workout plan ID to Workout plan object.
        """
        workout_plan = WorkoutPlan.query.get(workout_plan_id)
        if workout_plan is None:
            raise NotFound(f"Workout Plan with id :{workout_plan_id} not found.")
        return workout_plan

class PlaylistConverter(BaseConverter):
    """
    Converter for mapping playlist IDs to Playlist objects and vice versa.
    """

    def to_python(self, playlist_id):
        """
        Convert playlist ID to playlist object.
        """
        playlist = Playlist.query.get(playlist_id)
        if playlist is None:
            raise NotFound(f"Playlist with id :{playlist_id} not found.")
        return playlist

class UserConverter(BaseConverter):
    """
    Converter for mapping user IDs to User objects and vice versa.
    """

    def to_python(self, user_id):
        """
        Convert user ID to user object.
        """
        user = User.query.get(user_id)
        if user is None:
            raise NotFound(f"User with id :{user_id} not found.")
        return user
