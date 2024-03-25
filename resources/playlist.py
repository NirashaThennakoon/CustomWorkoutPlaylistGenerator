from flask import Response, jsonify, request, g
from flask_restful import Resource
from data_models.models import Playlist, PlaylistItem, Workout, Song
from extensions import db
from extensions import cache
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
import json

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
    def add_control_get_playlist(self, playlist_id):
        self.add_control(
            "playlist:get",
            href=f"/api/playlist/{playlist_id}",
            method="GET",
            title="Get Playlist by ID"
        )

    def add_control_edit_playlist(self, playlist_id):
        self.add_control(
            "playlist:edit",
            href=f"/api/playlist/{playlist_id}",
            method="PUT",
            title="Edit This Playlist",
            encoding="json",
            schema=Playlist.json_schema()
        )

    def add_control_delete_playlist(self, playlist_id):
        self.add_control(
            "playlist:delete",
            href=f"/api/playlist/{playlist_id}",
            method="DELETE",
            title="Delete This Playlist"
        )

    def add_control_add_playlist(self):
        self.add_control(
            "playlist:add",
            href="/api/playlist",
            method="POST",
            title="Add New Playlist",
            encoding="json",
            schema=Playlist.json_schema()
        )
MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
PLAYLIST_PROFILE = "/profiles/playlist/"  


def create_error_response(status_code, title, message=None):
    body = PlaylistBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)

class PlaylistResource(Resource):
    @cache.cached(timeout=60)
    def get(self, playlist_id):
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return create_error_response(404, "Playlist not found")

        playlist_builder = PlaylistBuilder()
        playlist_builder.add_namespace("playlist", PLAYLIST_PROFILE)
        playlist_builder.add_control_get_playlist(playlist_id)
        playlist_builder.add_control_edit_playlist(playlist_id)
        playlist_builder.add_control_delete_playlist(playlist_id)
        playlist_builder.add_control("profile", href=PLAYLIST_PROFILE)

        playlist_items = PlaylistItem.query.filter_by(playlist_id=playlist_id).all()
        songs_list = [Song.query.get(item.song_id) for item in playlist_items if item.song_id]

        playlist_dict = {
            "playlist_id": playlist.playlist_id,
            "playlist_duration": playlist.playlist_duration,
            "songs_list": [{
                "song_id": song.song_id,
                "song_name": song.song_name,
                "artist": song.song_artist,
                "genre": song.song_genre,
                "duration": song.song_duration
            } for song in songs_list if song]
        }

        playlist_builder.update(playlist_dict)
        return Response(json.dumps(playlist_builder), mimetype=MASON)
    
    # user can change the playlist song order
    def put(self, playlist_id):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400
        
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return {"message": "Playlist not found"}, 404
        
        try:
            validate(request.json, Playlist.json_schema(), format_checker=FormatChecker())

            if 'playlist_name' in data:
                playlist.playlist_name = data['playlist_name']
            if 'song_list' in data:
                song_order = data['song_list']
                # Delete existing records in the playlist_item table for the playlist id
                PlaylistItem.query.filter_by(playlist_id=playlist_id).delete()

                # Re-enter the incoming song ids with the updated order
                for index, song_id in enumerate(song_order):
                    playlist_item = PlaylistItem(
                        playlist_id=playlist_id,
                        song_id=song_id,
                    )
                    db.session.add(playlist_item)

            db.session.commit()
            cache.clear()
        except ValidationError as e:
                raise BadRequest(description=str(e))
        except ValueError as e:
            return {"message": str(e)}, 400
        return "", 204
    
    def delete(self, playlist_id):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")

        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return create_error_response(404, "Playlist not found")

        PlaylistItem.query.filter_by(playlist_id=playlist_id).delete()
        db.session.delete(playlist)
        db.session.commit()
        cache.clear()

        playlist_builder = PlaylistBuilder()
        playlist_builder["message"] = "Playlist deleted successfully"
        playlist_builder.add_control_get_playlist(playlist_id)  

        return Response(json.dumps(playlist_builder), 200, mimetype=MASON)

class CreatePlaylistResource(Resource):
    def post(self):
        data = request.json
        if not data or 'workout_ids' not in data:
            return create_error_response(400,"Invalid input data on CreatePlayList")          

        playlist_name_rec = data['playlist_name']
        workout_ids = data['workout_ids']

        songs_list = []
        total_workouts_duration = 0.0

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
        playlist = Playlist(playlist_duration=total_workouts_duration, playlist_name=playlist_name_rec)
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
        playlist_builder.add_control_get_playlist(playlist.playlist_id)
        playlist_builder["message"] = "Playlist created successfully"

        return Response(json.dumps(playlist_builder), status=201, mimetype=MASON)
