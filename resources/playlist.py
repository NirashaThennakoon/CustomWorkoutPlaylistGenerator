"""
   This module responsible for handling functions of playlist resources
"""
import json
from jsonschema import validate, ValidationError, FormatChecker
from flask import Response, request, g
from flask_restful import Resource
from data_models.models import Playlist, PlaylistItem, Workout, Song, WorkoutPlan
from extensions import db
from extensions import cache

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

class PlaylistBuilder(MasonBuilder):
    """
        A class for building playlist-related MASON hypermedia representations.
    """

    def add_control_get_song(self, playlist_id):
        """
            Adds a control to get songs for a playlist.
        """
        self.add_control(
            "item",
            href=f"/api/playlistItem/{playlist_id}",
            method="GET",
            title="Get songs for the playlist"
        )

    # def add_control_get_workout_plan(self, workout_plan_id):
    #     self.add_control(
    #         "custWorkoutPlaylistGen:workoutplan",
    #         href=f"/api/workoutPlan/{workout_plan_id}",
    #         method="GET",
    #         title="Get Workout plan by playlist"
    #     )

    def add_control_edit_playlist(self, playlist_id):
        """
            Adds a control to edit songs in a playlist.
        """
        self.add_control(
            "edit",
            href=f"/api/playlist/{playlist_id}",
            method="PUT",
            title="Edit This Playlist",
            encoding="json",
            schema=Playlist.json_schema()
        )

    def add_control_delete_playlist(self, playlist_id):
        """
            Adds a control to delete a playlist.
        """
        self.add_control(
            "delete",
            href=f"/api/playlist/{playlist_id}",
            method="DELETE",
            title="Delete This Playlist"
        )

MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
PLAYLIST_PROFILE = "/profile"  
LINK_RELATION = "/playlist_link_relation"

def create_error_response(status_code, title, message=None):
    """
        Creates an error response with a MASON hypermedia representation.
    """
    body = PlaylistBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)

class PlaylistResource(Resource):
    """
        This resource includes the playlist GET, PUT and DELETE endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, playlist):
        """
            Retrieve details of a playlist.

            This method retrieves the details of a playlist including its ID, duration, 
            and the list of songs it contains. The playlist and its associated songs
            are retrieved from the database.
        """

        playlist_builder = PlaylistBuilder()
        playlist_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
        playlist_builder.add_control_get_song(playlist.playlist_id)
        playlist_builder.add_control_edit_playlist(playlist.playlist_id)
        playlist_builder.add_control_delete_playlist(playlist.playlist_id)
        playlist_builder.add_control("profile", href=PLAYLIST_PROFILE)

        playlist_items = PlaylistItem.query.filter_by(playlist_id=playlist.playlist_id).all()
        songs_list = []
        for item in playlist_items:
            song = Song.query.get(item.song_id)
            if song:
                song_dict = {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "artist": song.song_artist,
                    "genre": song.song_genre,
                    "duration": song.song_duration
                }
            songs_list.append(song_dict)

        playlist_dict = {}

        if playlist:
            playlist_dict = {
            "playlist_name": playlist.playlist_name,
            "playlist_id": playlist.playlist_id,
            "playlist_duration": playlist.playlist_duration,
            "songs_list": songs_list
            }
        for key, value in playlist_dict.items():
            playlist_builder[key] = value
        return Response(json.dumps(playlist_builder), 200, mimetype=MASON)

    # user can change the playlist song order
    def put(self, playlist):
        """
            Update a playlist.
            This method updates the details of a playlist based on the provided JSON data.
        """
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")
        if MASON != "application/vnd.mason+json":
            return create_error_response(415, "Unsupported Media Type", "This service accept JSON input.")
        data = request.json
        if not data:
            return create_error_response(400, "No input data provided")
        if not playlist:
            return create_error_response(404, "Playlist not found")
        try:
            validate(request.json, Playlist.json_schema(), format_checker=FormatChecker())

            if 'playlist_name' in data:
                playlist.playlist_name = data['playlist_name']
            if 'song_list' in data:
                song_order = data['song_list']
                # Delete existing records in the playlist_item table for the playlist id
                PlaylistItem.query.filter_by(playlist_id=playlist.playlist_id).delete()

                # Re-enter the incoming song ids with the updated order
                for index, song_id in enumerate(song_order):
                    playlist_item = PlaylistItem(
                        playlist_id=playlist.playlist_id,
                        song_id=song_id,
                    )
                    db.session.add(playlist_item)

            db.session.commit()
            cache.clear()

            playlist_builder = PlaylistBuilder()
            playlist_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            playlist_builder.add_control("profile", href=PLAYLIST_PROFILE)
            playlist_builder["message"] = "Workout updated successfully"

            return Response(json.dumps(playlist_builder), 204, mimetype=MASON)

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))

    def delete(self, playlist):
        """
            Delete a playlist and its associated items.

            This method deletes the specified playlist along with all its associated items.

        """
        workoutplan = WorkoutPlan.query.filter_by(playlist_id=playlist.playlist_id).all()
        if workoutplan:
            return create_error_response(403, "This playlist belongs to a workout plan")
        
        playlist_items = PlaylistItem.query.filter_by(playlist_id=playlist.playlist_id).all()

        # Delete playlist items
        for item in playlist_items:
            db.session.delete(item)

        # Delete playlist
        db.session.delete(playlist)
        db.session.commit()
        cache.clear()

        playlist_builder = PlaylistBuilder()
        playlist_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
        playlist_builder.add_control("profile", href=PLAYLIST_PROFILE)
        playlist_builder["message"] = "Workout deleted successfully"

        return Response(json.dumps(playlist_builder), 204, mimetype=MASON)

class PlaylistCreation(Resource):
    """
        Resource for creating playlists based on workout IDs.

        This class defines a resource for creating playlists based on workout IDs provided
        in the request JSON data. It handles the creation of playlists with songs selected
        according to the intensity of each workout.
    """
    def post(self):
        """
            Create a playlist based on provided workout IDs.

            This method creates a playlist based on the workout IDs provided in
            the request JSON data. The playlist is created with songs selected
            according to the intensity of each workout.
        """
        data = request.json
        if not data or 'workout_ids' not in data:
            return create_error_response(400,"Invalid input data on CreatePlayList")

        if MASON != "application/vnd.mason+json":
            return create_error_response(415, "Unsupported Media Type", "This service accept JSON input.")
        
        playlist_name_rec = data['playlist_name']
        workout_ids = data['workout_ids']

        songs_list = []
        total_workouts_duration = 0.0
        try:
            # Add songs to playlist for each workout
            for workout_id in workout_ids:
                workout = Workout.query.get(workout_id)
                if workout:
                    duration = workout.duration
                    intensity = workout.workout_intensity
                    genre = ""

                    # Determine genre based on intensity
                    if intensity == "slow":
                        genre = ["Ambient", "Classical", "Jazz"]
                    elif intensity == "mild":
                        genre = ["Pop", "R&B", "Indie"]
                    elif intensity == "intermediate":
                        genre = ["Rock", "Hip-hop", "EDM"]
                    elif intensity == "fast":
                        genre = ["Techno", "Dance", "House"]
                    elif intensity == "extreme":
                        genre = ["Metal", "Hardcore", "Dubstep"]

                    # Get songs based on workout duration and genre
                    songs = Song.query.filter(Song.song_genre.in_(genre)).all()
                    temp_duration = 0.0
                    for song in songs:
                        song_dict = {
                            "song_id": song.song_id
                        }
                        songs_list.append(song_dict)
                        temp_duration += song.song_duration
                        if temp_duration >= duration:
                            break
                    total_workouts_duration = total_workouts_duration + temp_duration

            # Create playlist
            playlist = Playlist(playlist_duration=total_workouts_duration,
                                playlist_name=playlist_name_rec)
            db.session.add(playlist)
            db.session.commit()

            # Add songs related to playlist to playlist_item table
            for song in songs_list:
                playlist_item = PlaylistItem(
                    playlist_id=playlist.playlist_id,
                    song_id=song['song_id'],
                )
                db.session.add(playlist_item)
            db.session.commit()
            cache.clear()

            playlist_builder = PlaylistBuilder()
            playlist_builder.add_namespace("custWorkoutPlaylistGen", LINK_RELATION)
            playlist_builder.add_control("profile", href=PLAYLIST_PROFILE)
            playlist_builder["message"] = "Playlist created successfully"
            playlist_builder["playlist_id"] = playlist.playlist_id

            return Response(json.dumps(playlist_builder), status=201, mimetype=MASON)
        except Exception as e:
            return create_error_response(500, "Internal Server Error", str(e))

class PlaylistItemResource(Resource):
    """
        This resource includes the GET playlist items endpoint.
    """
    @cache.cached(timeout=60)
    def get(self, playlist_id):
        """
            Retrieve information about playlist items for a given playlist ID.

            Args:
                playlist_id: The ID of the playlist
                items are to be retrieved.

            Returns:
                A tuple containing a list of dictionaries representing playlist
                item details and an HTTP status code. Each dictionary in the list
                contains keys 'playlist_id' and 'song_id', populated with
                corresponding values from each playlist item.
        """
        playlistItem_list = []
        try:
            playlistItems = PlaylistItem.query.filter_by(playlist_id=playlist_id).all()
            playlist_builder = PlaylistBuilder()
            for playlistItem in playlistItems:
                playlist_dict = {
                    "playlist_id": playlistItem.playlist_id,
                    "song_id": playlistItem.song_id
                }
                playlistItem_list.append(playlist_dict)
            playlist_builder["Song list"] = playlistItem_list

            return Response(json.dumps(playlist_builder), mimetype=MASON)
        except Exception as e:
            return create_error_response(500, "Internal Server Error", str(e))
