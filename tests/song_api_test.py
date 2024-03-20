import json
import pytest
import random
from .. import create_app 
from flask.testing import FlaskClient 
from data_models.models import Song
from extensions import db
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/song/' 

def test_get_song(client):
    response = client.get(f'{RESOURCE_URL}1/')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1

def test_get_songs(client):
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) != 0

def test_post_song(client):
        valid = _get_song_json()
        invalid = _get_song_with_string_duration_json()

        # test with wrong content type
        resp = client.post(RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        
        # send same data again for 409
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 409

        #send non-float for duration of song
        resp = client.post(RESOURCE_URL, json=invalid)
        assert resp.status_code == 400

        # remove workout_name field for 400
        valid.pop("song_name")
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 400

def test_put_song(client):
        valid = _get_song_json()

        # test with wrong content type
        resp = client.put(f'{RESOURCE_URL}1/', data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # test with none
        resp = client.put(f'{RESOURCE_URL}1/', data = None, headers=Headers({"Content-Type": "application/json"}))
        assert resp.status_code== 400

        #test with wrong id
        resp = client.put(f'{RESOURCE_URL}id/', json=valid)
        assert resp.status_code == 404
        
        # test with not avaliable id
        resp = client.put(f'{RESOURCE_URL}10000/', json=valid)
        assert resp.status_code == 404
        
        # test with valid
        resp = client.put(f'{RESOURCE_URL}1/', json=valid)
        assert resp.status_code == 200
        
        # remove field
        valid.pop("song_name")
        resp = client.put(f'{RESOURCE_URL}1/', json=valid)
        assert resp.status_code == 200

def test_delete_song(client):
        resp = client.delete(f'{RESOURCE_URL}2/')
        assert resp.status_code == 200
        resp = client.delete(f'{RESOURCE_URL}2/')
        assert resp.status_code == 404
        resp = client.delete(f'{RESOURCE_URL}id/')
        assert resp.status_code == 404

def _get_song_json():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "song_name": "Sample Song 1",
        "song_artist": "Taylor",
        "song_genre": "pop",
        "song_duration": 56.7
    }

def _get_song_with_string_duration_json():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "song_name": "Sample Song 2",
        "song_artist": "Taylor",
        "song_genre": "pop",
        "song_duration": "56.7"
    }

