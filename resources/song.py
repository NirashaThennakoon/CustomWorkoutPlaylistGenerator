"""
   This module responsible for handling functions related to song resource
"""
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import BadRequest
from flask import request, g
from flask_restful import Resource
from data_models.models import Song
from extensions import db
from extensions import cache


class SongResource(Resource):
    """
        This resource includes the songs GET, PUT and DELETE endpoints.
    """
    @cache.cached(timeout=60)
    def get(self, song):
        """
            This method fetches details about a given song andreturns
            them in a list format.
            Args: 
                song: An object representing the song for which
                information is to be retrieved.
            Returns:
                A tuple containing a list of dictionaries
                representing song details and an HTTP status code.
        """
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
        return songs_list, 200

    def put(self, song):
        """
            This method updates details about a given song if
            the user has admin privileges.
            Args:
                song: An object representing the song to be updated.
            Returns:
                A tuple containing a dictionary with a message indicating
                the success of the operation and an HTTP status code.
                If the operation is successful, the status code is 200.
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403
        data = request.json
        if not data:
            return {"message": "No input data provided"}, 400
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
            raise BadRequest(description=str(e)) from e
        except ValueError as e:
            return {"message": "Invalid input data: " + str(e)}, 400

        return {"message": "Song updated successfully"}, 200

    def delete(self, song):
        """
            This method deletes details about a given song if the
            user has admin privileges.
            Args:
                song: An object representing the song to be deleted.
            Returns:
                A tuple containing a dictionary with a message indicating
                the success of the operation and an HTTP status code.
                If the operation is successful, the status code is 200.
        """
        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403

        db.session.delete(song)
        db.session.commit()
        cache.clear()
        return {"message": "Song deleted successfully"}, 200

class SongsCollection(Resource):
    """
        This resource includes the GET all songs and POST a song endpoints.
    """
    @cache.cached(timeout=60)
    def get(self):
        """
            This method fetches details about all available songs
            and returns them in a list format.            
            Returns:
                A tuple containing a list of dictionaries representing song
                details and an HTTP status code. Each dictionary in the list contains keys
                'song_id', 'song_name', 'song_artist', 'song_genre', and 'song_duration'
                populated with corresponding values from the database. 
                The status code indicates the success of the operation
                (200 for successful retrieval).
        """
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

        return songs_list, 200

    def post(self):
        """
            This method adds a new song to the system based on the provided data.
            Returns:
                A tuple containing a dictionary with a message indicating
                the success of the operation and an HTTP status code.
                If the operation is successful, the status code is 201.
        """

        if g.current_api_key.user.user_type != 'admin':
            return {"message": "Unauthorized access"}, 403

        data = request.json

        try:
            validate(request.json, Song.json_schema(), format_checker=FormatChecker())
        except ValidationError as e:
            raise BadRequest(description=str(e)) from e

        if (data['song_duration'] is not None and not isinstance(data['song_duration'], float)):
            return {"message": "Song duration must be a float"}, 400

        song_name = data['song_name']
        existing_song = Song.query.filter_by(song_name=song_name).first()
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
