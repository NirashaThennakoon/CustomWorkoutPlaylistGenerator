import hashlib
import click

from flask.cli import with_appcontext
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), nullable=False)
    password = db.Column(db.String(64), nullable=False)
    height = db.Column(db.Float, nullable=False)
    weight = db.Column(db.Float, nullable=False)
    user_type = db.Column(db.String(32), nullable=False)
    user_token = db.Column(db.String(64), nullable=False)
    token_expiration = db.Column(db.DateTime, nullable=False)
    
    api_key = db.relationship("ApiKey", back_populates="user", cascade="all, delete-orphan")
    workout_plan = db.relationship("WorkoutPlan", back_populates="user")

    @staticmethod
    def password_hash(password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, password):
        hashed_password = User.password_hash(password)
        return self.password == hashed_password

    def json_schema():
        schema = {
            "type": "object",
            "required": ["email", "password", "height", "weight", "user_type"]
        }
        props = schema["properties"] = {}
        props["email"] = {
            "description": "Users email",
            "type": "string"
        }
        props["password"] = {
            "description": "Users password",
            "type": "string"
        }
        props["height"] = {
            "description": "Users height",
            "type": "number"
        }
        props["weight"] = {
            "description": "Users weight",
            "type": "number"
        }
        props["user_type"] = {
            "description": "Users type",
            "type": "string"
        }
        return schema

class Workout(db.Model):
    workout_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workout_name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    workout_intensity = db.Column(db.String(32), nullable=False)
    equipment = db.Column(db.String(64), nullable=False)
    workout_type = db.Column(db.String(64), nullable=False)

    workout_plan_item = db.relationship("WorkoutPlanItem", back_populates="workout")

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["workout_name", "duration", "workout_intensity", "equipment", "workout_type"]
        }
        props = schema["properties"] = {}
        props["workout_name"] = {
            "description": "Name of the workout",
            "type": "string"
        }
        props["duration"] = {
            "description": "Duration of the workout",
            "type": "number"
        }
        props["workout_intensity"] = {
            "description": "Intensity of the workout",
            "type": "string"
        }
        props["equipment"] = {
            "description": "Equipment needed for the workout",
            "type": "string"
        }
        props["workout_type"] = {
            "description": "Type of the workout",
            "type": "string"
        }
        return schema

class WorkoutPlanItem(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.workout_plan_id"))
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.workout_id"))

    workout_plan = db.relationship("WorkoutPlan", back_populates="workout_plan_item")
    workout = db.relationship("Workout", back_populates="workout_plan_item")

class WorkoutPlan(db.Model):
    workout_plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.playlist_id"))

    workout_plan_item = db.relationship("WorkoutPlanItem", back_populates="workout_plan")
    user = db.relationship("User", back_populates="workout_plan")
    playlist = db.relationship("Playlist", back_populates="workout_plan")

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["plan_name", "duration"]
        }
        props = schema["properties"] = {}
        props["plan_name"] = {
            "description": "Name of the workout plan",
            "type": "string"
        }
        props["duration"] = {
            "description": "Duration of the workout plan",
            "type": "number"
        }
        return schema

class Playlist(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_duration = db.Column(db.Float, nullable=False)
    playlist_name = db.Column(db.String(64), nullable=False)

    playlist_item = db.relationship("PlaylistItem", back_populates="playlist")
    workout_plan = db.relationship("WorkoutPlan", back_populates="playlist") 

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["playlist_name", "playlist_duration"]
        }
        props = schema["properties"] = {}
        props["playlist_name"] = {
            "description": "Name of the playlist",
            "type": "string"
        }
        props["playlist_duration"] = {
            "description": "Duration of the playlist",
            "type": "number"
        }
        return schema 

class PlaylistItem(db.Model):
    item_id = db.Column(db.Integer, primary_key=True)
    song_id = db.Column(db.Integer, db.ForeignKey("song.song_id"))
    playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.playlist_id"))

    song = db.relationship("Song", back_populates="playlist_item")
    playlist = db.relationship("Playlist", back_populates="playlist_item")

class Song(db.Model):
    song_id = db.Column(db.Integer, primary_key=True)
    song_name = db.Column(db.String(64), nullable=False)
    song_artist = db.Column(db.String(64), nullable=False)
    song_genre = db.Column(db.String(64), nullable=False)
    song_duration = db.Column(db.Float, nullable=False)

    playlist_item = db.relationship("PlaylistItem", back_populates="song")

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["song_name", "song_artist", "song_genre", "song_duration"]
        }
        props = schema["properties"] = {}
        props["song_name"] = {
            "description": "Name of the song",
            "type": "string"
        }
        props["song_artist"] = {
            "description": "Artist of the song",
            "type": "string"
        }
        props["song_genre"] = {
            "description": "Genre of the song",
            "type": "string"
        }
        props["song_duration"] = {
            "description": "Duration of the song",
            "type": "number"
        }
        return schema 

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    admin =  db.Column(db.Boolean, default=False)
    
    user = db.relationship("User", back_populates="api_key", uselist=False)
    
    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()
    
@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()