from flask import jsonify, request, url_for, g
from flask_restful import Resource
from data_models.models import Song
from extensions import db
from extensions import cache
from sqlalchemy.exc import IntegrityError
from resources.playlist import CreatePlaylistResource
import requests
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType


class SongResource(Resource):
    @cache.cached(timeout=60)
    def get(self, song):           
        try:
            songs_list = []
            if song:
                song_dict = {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "song_artist": song.song_artist,
                    "song_genre": song.song_genre,
                    "song_duration": song.song_duration,
                }
                songs_list.append(song_dict)
        except KeyError:
            return jsonify({"message": "Invalid input data"}), 400
        return songs_list, 200

    def put(self, song):

        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400
        if not song:
            return {"message": "Song not found"}, 404

        try:         
            validate(request.json, Song.json_schema(), format_checker=FormatChecker())
            
            if 'song_name' in data:
                song.song_name = data['song_name']
            if 'song_artist' in data:
                song.song_artist = data['song_artist']
            if 'song_genre' in data:
                song.song_genre = data['song_genre']
            if 'song_duration' in data:
                song.song_duration = data['song_duration']

            db.session.commit()
            cache.clear()
        except ValidationError as e:
                raise BadRequest(description=str(e))
        except ValueError as e:
            return {"message": "Invalid input data: " + str(e)}, 400

        return {"message": "Song updated successfully"}, 200

    def delete(self, song):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        if not song:
            return {"message": "Song not found"}, 404

        db.session.delete(song)
        db.session.commit()
        cache.clear()
        return {"message": "Song deleted successfully"}, 200
    

class SongListResource(Resource):
    @cache.cached(timeout=60)
    def get(self):           
        try:
            songs = Song.query.all()
            songs_list = []
            for song in songs:
                song_dict = {
                    "song_id": song.song_id,
                    "song_name": song.song_name,
                    "song_artist": song.song_artist,
                    "song_genre": song.song_genre,
                    "song_duration": song.song_duration,
                }
                songs_list.append(song_dict)
        except KeyError:
            return jsonify({"message": "Invalid input data"}), 400
        return songs_list, 200
    
    def post(self):
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        
        data = request.json

        try:
            validate(request.json, Song.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            raise BadRequest(description=str(e))
            
        if (data['song_duration'] is not None and not isinstance(data['song_duration'], float)):
            return {"message": "Song duration must be a float"}, 400

        songName = data['song_name']
        existing_song = Song.query.filter_by(song_name=songName).first()
        if existing_song:
            return {"error": "Song already exists"}, 409

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
        except ValueError as e:
            return {"message": str(e)}, 400

        return {"message": "Song added successfully"}, 201

