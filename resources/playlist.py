from flask import jsonify, request, g
from flask_restful import Resource
from data_models.models import Playlist, PlaylistItem, Workout, Song
from extensions import db
from extensions import cache
from jsonschema import validate, ValidationError, FormatChecker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType


class PlaylistResource(Resource):
    @cache.cached(timeout=60)
    def get(self, playlist_id):
        playlist = Playlist.query.get(playlist_id)
        playlist_items = PlaylistItem.query.filter_by(playlist_id=playlist_id).all()
               
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
            "playlist_id": playlist.playlist_id,
            "playlist_duration": playlist.playlist_duration,
            "songs_list": songs_list
            }
        return jsonify(playlist_dict)
    
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
        playlist = Playlist.query.get(playlist_id)
        if not playlist:
            return {"message": "Playlist not found"}, 404

        playlist_items = PlaylistItem.query.filter_by(playlist_id=playlist_id).all()

        # Delete playlist items
        for item in playlist_items:
            db.session.delete(item)

        # Delete playlist
        db.session.delete(playlist)
        db.session.commit()
        cache.clear()

        return "", 204


class CreatePlaylistResource(Resource):
    def post(self):
        data = request.json
        if not data or 'workout_ids' not in data:
            return {"message": "Invalid input data on CreatePlayList"}, 400            

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

        return {"message": "Playlist created successfully", "playlist_id": playlist.playlist_id}, 201
