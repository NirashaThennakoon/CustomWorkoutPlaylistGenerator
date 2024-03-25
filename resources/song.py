from flask import Response, jsonify, request, url_for, g
from flask_restful import Resource
from data_models.models import Song
from extensions import db
from extensions import cache
from sqlalchemy.exc import IntegrityError
from resources.playlist import CreatePlaylistResource
import requests
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
        
class SongBuilder(MasonBuilder):
    def add_control_all_songs(self):
        self.add_control(
            "song:all",
            href="/api/song",
            method="GET",
            title="List All Songs"
        )
        
    def add_control_get_song(self, song_id):
        self.add_control(
            "song:get",
            href=f"/api/song/{song_id}",
            method="GET",
            title="Get Song by song_id"
        )
        
    def add_control_add_song(self):
        self.add_control(
            "song:add",
            href="/api/song",
            method="POST",
            title="Add New Song",
            encoding="json",
            schema=Song.json_schema()
        )
        
    def add_control_edit_song(self, song_id):
        self.add_control(
            "song:edit",
            href=f"/api/song/{song_id}",
            method="PUT",
            title="Edit This Song",
            encoding="json",
            schema=Song.json_schema()
        )
        
    def add_control_delete_song(self, song_id):
        self.add_control(
            "song:delete",
            href=f"/api/song/{song_id}",
            method="DELETE",
            title="Delete This Song"
        )
MASON = "application/vnd.mason+json"
ERROR_PROFILE = "/profiles/error/"
SONG_PROFILE = "/profiles/song/"  

def create_error_response(status_code, title, message=None):
    body = SongBuilder()
    body.add_error(title, message if message else "")
    return Response(json.dumps(body), status_code, mimetype=MASON)

class SongResource(Resource):
    @cache.cached(timeout=60)
    def get(self, song_id):           
        song = Song.query.get(song_id)
        if not song:
            return create_error_response(404, "Song not found")

        song_builder = SongBuilder()
        song_builder.add_namespace("song", SONG_PROFILE)
        song_builder.add_control_get_song(song_id)
        song_builder.add_control_edit_song(song_id)
        song_builder.add_control_delete_song(song_id)
        song_builder.add_control("profile", href=SONG_PROFILE)

        song_dict = {
            "song_id": song.song_id,
            "song_name": song.song_name,
            "song_artist": song.song_artist,
            "song_genre": song.song_genre,
            "song_duration": song.song_duration,
        }
        for key, value in song_dict.items():
            song_builder[key] = value
        return Response(json.dumps(song_builder), mimetype=MASON)

    def put(self, song_id):

        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")
        
        data = request.json
        if not data:
            return create_error_response(400, "No input data provided")
        song = Song.query.get(song_id)
        if not song:
            return create_error_response(404, "Song not found")

        try:         
            validate(request.json, Song.json_schema(), format_checker=FormatChecker())
            
            song.song_name = data.get('song_name', song.song_name)
            song.song_artist = data.get('song_artist', song.song_artist)
            song.song_genre = data.get('song_genre', song.song_genre)
            song.song_duration = data.get('song_duration', song.song_duration)

            db.session.commit()
            cache.clear()

            song_builder = SongBuilder()
            song_builder.add_namespace("song", SONG_PROFILE)
            song_builder.add_control_get_song(song_id)
            song_builder.add_control_edit_song(song_id)
            song_builder.add_control_delete_song(song_id)
            song_builder.add_control("profile", href=SONG_PROFILE)
            song_builder["message"] = "Song updated successfully"

            return Response(json.dumps(song_builder), 200, mimetype=MASON)

        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
        except ValueError as e:
            return create_error_response(400, "Invalid input data", str(e))

    def delete(self, song_id):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")
        song = Song.query.get(song_id)
        if not song:
            return create_error_response(404, "Song not found")

        db.session.delete(song)
        db.session.commit()
        cache.clear()

        song_builder = SongBuilder()
        song_builder["message"] = "Song deleted successfully"
        
        song_builder.add_control_all_songs()

        return Response(json.dumps(song_builder), 200, mimetype=MASON)
    
class SongListResource(Resource):
    @cache.cached(timeout=60)
    def get(self): 
        song_builder = SongBuilder()
        song_builder.add_namespace("song", SONG_PROFILE)
        song_builder.add_control_add_song()  
        songs = Song.query.all()
        items = []
        for song in songs:
            item = SongBuilder()
            item.add_control_get_song(song.song_id)
            item.add_control_edit_song(song.song_id)
            item.add_control_delete_song(song.song_id)
            item.add_control("profile", href=SONG_PROFILE)
            
            item.update({
                "song_id": song.song_id,
                "song_name": song.song_name,
                "song_artist": song.song_artist,
                "song_genre": song.song_genre,
                "song_duration": song.song_duration,
            })
            items.append(item)
        
        song_builder["items"] = items
        song_builder.add_control("self", href="/api/song/", title="Self")
        return Response(json.dumps(song_builder), 200, mimetype=MASON)
    
    def post(self):
        if g.current_api_key.user.user_type != 'admin':
            return create_error_response(403, "Unauthorized access")
        
        data = request.json

        try:
            validate(request.json, Song.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))
            
        if (data['song_duration'] is not None and not isinstance(data['song_duration'], float)):
            return create_error_response(400, "Song duration must be a float")

        songName = data['song_name']
        existing_song = Song.query.filter_by(song_name=songName).first()
        if existing_song:
            return create_error_response(400, "Song already exists")

        try:
            song = Song(
                song_name=data['song_name'],
                song_artist=data['song_artist'],
                song_genre=data['song_genre'],
                song_duration=data['song_duration']
            )

            db.session.add(song)
            db.session.commit()
            cache.clear()
            
            song_builder = SongBuilder()
            song_builder.add_namespace("song", SONG_PROFILE)
            song_builder.add_control_get_song(song.song_id)
            song_builder.add_control("profile", href=SONG_PROFILE)
            song_builder["message"] = "Song added successfully"
            
            return Response(json.dumps(song_builder), status=201, mimetype=MASON)
        except Exception as e: 
            return create_error_response(500, "Internal Server Error", str(e))

