import hashlib
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

    api_key = db.relationship("ApiKey", back_populates="user")
    # workout_plan = db.relationship("WorkoutPlan", back_populates="user")

class Workout(db.Model):
    workout_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workout_name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Float, nullable=False)
    workout_intensity = db.Column(db.String(32), nullable=False)
    equipment = db.Column(db.String(64), nullable=False)
    workout_type = db.Column(db.String(64), nullable=False)

    workout_plan_item = db.relationship("WorkoutPlanItem", back_populates="workout")

class WorkoutPlanItem(db.Model):
    item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    workout_plan_id = db.Column(db.Integer, db.ForeignKey("workout_plan.workout_plan_id"))
    workout_id = db.Column(db.Integer, db.ForeignKey("workout.workout_id"))

    workout_plan = db.relationship("WorkoutPlan", back_populates="workout_plan_item")
    workout = db.relationship("Workout", back_populates="workout_plan_item")

class WorkoutPlan(db.Model):
    workout_plan_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_name = db.Column(db.String(64), nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, nullable=False)
    playlist_id = db.Column(db.Integer, nullable=False)
    # user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    # playlist_id = db.Column(db.Integer, db.ForeignKey("playlist.playlist_id"), nullable=True)

    workout_plan_item = db.relationship("WorkoutPlanItem", back_populates="workout_plan")
    # user = db.relationship("User", back_populates="workout_plan")
    # playlist = db.relationship("Playlist", back_populates="workout_plan")

class Playlist(db.Model):
    playlist_id = db.Column(db.Integer, primary_key=True)
    playlist_duration = db.Column(db.Float, nullable=False)

    playlist_item = db.relationship("PlaylistItem", back_populates="playlist")
    # workout_plan = db.relationship("WorkoutPlan", back_populates="playlist")  

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
     
class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(32), nullable=False, unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    admin =  db.Column(db.Boolean, default=False)
    
    user = db.relationship("User", back_populates="api_key", uselist=False)
    
    @staticmethod
    def key_hash(key):
        return hashlib.sha256(key.encode()).digest()