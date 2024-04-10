"""
This module is responsible for app configuration and db population for test
"""
import hashlib
import datetime
import random
import uuid
import pytest
from flask.testing import FlaskClient 
from werkzeug.datastructures import Headers
from extensions import db
from data_models.models import (
    Workout, Playlist, Song, WorkoutPlan, User, 
    ApiKey, WorkoutPlanItem, PlaylistItem
)
from .. import create_app 

def generate_api_key():
    return str(uuid.uuid4())

TEST_ADMIN_KEY = 'eaecf80e-3b2a-48b8-94c2-d754cf38'
TEST_USER_KEY = '1baf9207-4e72-4de8-b30b-fbbbbef5'

@pytest.fixture(scope='session')
def client():
    config = {
        "SQLALCHEMY_DATABASE_URI": (
            "mysql+mysqldb://admin:pwpdb7788@"
            "workoutplaylists.cpcoaea0i7dq."
            "us-east-1.rds.amazonaws.com/"
            "test_workout_playlists"
        ),
        "TESTING": True
    }

        
    app = create_app(config)
    
    with app.app_context():
        db.drop_all()
        db.create_all()
        _populate_db()
        
    app.test_client_class = AuthHeaderClient
    yield app.test_client()
    
class AuthHeaderClient(FlaskClient):
    
    def open(self, *args, **kwargs):
        api_key_headers = Headers({
            'X-API-Key': TEST_ADMIN_KEY
        })
        headers = kwargs.pop('headers', Headers())
        headers.extend(api_key_headers)
        kwargs['headers'] = headers

        # Explicitly enable redirect following
        kwargs['follow_redirects'] = True
        return super().open(*args, **kwargs)

def _populate_db():
    populate_user_api_key_tables()
    populate_workout_table()
    for i in range(1, 6):
        p = Playlist(
            playlist_duration=random.random(),
            playlist_name=f"test-workout-plan-{i} Playlist"
        )
        song_artist_list = ["Taylor Swift","Drake","Ed Sheeran","Billie Eilish"]
        song_genre_list = ["classic", "pop", "falk", "country"]
        s = Song(
            song_name=f"test-song-{i}",
            song_artist=random.choice(song_artist_list),
            song_genre=random.choice(song_genre_list),
            song_duration=random.random()
        )
        playlist_item = PlaylistItem(
            song_id = i,
            playlist_id= i
        )

        db.session.add(s)
        db.session.add(p)
        db.session.add(playlist_item)
    
        
    wp1 = WorkoutPlan(
            plan_name="test-workout-plan-1",
            duration=random.random(),
            user_id= 1,
            playlist_id=1
    )
    wp_item1 = WorkoutPlanItem(
        workout_plan_id= 1,
        workout_id = 1
    )
    db.session.add(wp1)
    db.session.add(wp_item1)
    wp2 = WorkoutPlan(
            plan_name="test-workout-plan-2",
            duration=random.random(),
            user_id= 2,
            playlist_id=2
    )
    wp_item2 = WorkoutPlanItem(
        workout_plan_id= 2,
        workout_id = 2
    )
    db.session.add(wp2)
    db.session.add(wp_item2)
    wp3 = WorkoutPlan(
            plan_name="test-workout-plan-3",
            duration=random.random(),
            user_id= 3,
            playlist_id=3
    )
    wp_item3 = WorkoutPlanItem(
        workout_plan_id= 3,
        workout_id = 3
    )
    db.session.add(wp3)
    db.session.add(wp_item3)
    db.session.commit()   

def populate_user_api_key_tables():
    """
    populate user and api key tables
    """
    token_expiration = datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    u1 = User(
            email="test-email-1@gmail.com",
            password= User.password_hash("testPassword1"),
            height= random.random(),
            weight= random.random(),
            user_type= 'admin',
            user_token= hashlib.sha256("test-email-1@gmail.com".encode()).hexdigest(),
            token_expiration=token_expiration
    )
    db.session.add(u1)
    api_key1 = ApiKey(key=TEST_ADMIN_KEY, user_id=1, admin=True)
    db.session.add(api_key1)

    u2 = User(
            email="test-email-2@gmail.com",
            password= User.password_hash("testPassword2"),
            height= random.random(),
            weight= random.random(),
            user_type= 'user',
            user_token= hashlib.sha256("test-email-2@gmail.com".encode()).hexdigest(),
            token_expiration=token_expiration
    )
    db.session.add(u2)
    api_key2 = ApiKey(key=TEST_USER_KEY, user_id=2, admin=False)
    db.session.add(api_key2)

    u3 = User(
            email="test-email-3@gmail.com",
            password= User.password_hash("testPassword2"),
            height= random.random(),
            weight= random.random(),
            user_type= 'user',
            user_token= hashlib.sha256("test-email-3@gmail.com".encode()).hexdigest(),
            token_expiration=token_expiration
    )
    db.session.add(u3)
    api_key3 = ApiKey(key=generate_api_key(), user_id=3, admin=False)
    db.session.add(api_key3)

def populate_workout_table():
    w1 = Workout(
        workout_name="test-workout-1",
        duration=10.36,
        workout_intensity="slow",
        equipment="threadmill",
        workout_type="running"
    )
    w2 = Workout(
        workout_name="test-workout-2",
        duration=12.54,
        workout_intensity="mild",
        equipment="rwoing machine",
        workout_type="strength"
    )
    w3 = Workout(
        workout_name="test-workout-3",
        duration=52.30,
        workout_intensity="intermediate",
        equipment="rwoing machine",
        workout_type="strength"
    )
    w4 = Workout(
        workout_name="test-workout-4",
        duration=20.38,
        workout_intensity="fast",
        equipment="threadmill",
        workout_type="running"
    )
    w5 = Workout(
        workout_name="test-workout-5",
        duration=45.27,
        workout_intensity="extreme",
        equipment="cardio equipment",
        workout_type="cardio"
    )

    db.session.add(w1)
    db.session.add(w2)
    db.session.add(w3)
    db.session.add(w4)
    db.session.add(w5)
