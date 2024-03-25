"""
    This module is for test funstionalities of Song reaource
"""
import json
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/song/'
def test_get_song(client):
    """
        Test get request 
    """
    # get song with id 1
    response = client.get(f'{RESOURCE_URL}1/')
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1
    print(data)
    assert data[0]["song_name"] == "test-song-1"

def test_get_all_songs(client):
    """
        Test get all request 
    """
    #get all songs
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 5

def test_post_song(client):
    """
        Test post request 
    """
    valid = _get_song_json()
    invalid = _get_song_with_string_duration_json()

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid data
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["message"] == "Song added successfully"
    # send same data again for 409
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 409
    data = json.loads(resp.data)
    assert data["error"] == "Song already exists"

    #send non-float for duration of song
    resp = client.post(RESOURCE_URL, json=invalid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["message"] == "Song duration must be a float"

    # remove workout_name field for 400
    valid.pop("song_name")
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

def test_post_song_db_error(client, mocker):
    """
        Test post request when db error occurs
    """
    #test when ValueErorr occured
    valid = _get_song2_json()

    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = ValueError("Mocked exception")

    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["message"] == "Mocked exception"

def test_put_song(client):
    """
        Test put request 
    """
    valid = _get_song_json()

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}1/', data="notjson",
                        headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test with none
    resp = client.put(f'{RESOURCE_URL}1/', json={})
    assert resp.status_code== 400
    data = json.loads(resp.data)
    assert data["message"] == "No input data provided"
    # test with not avaliable id
    resp = client.put(f'{RESOURCE_URL}10000/', json=valid)
    assert resp.status_code == 404
    # test with valid
    resp = client.put(f'{RESOURCE_URL}1/', json=valid)
    assert resp.status_code == 200
    data = json.loads(resp.data)
    assert data["message"] == "Song updated successfully"
    # remove field
    valid.pop("song_name")
    resp = client.put(f'{RESOURCE_URL}1/', json=valid)
    assert resp.status_code == 400

def test_put_song_with_db_error(client, mocker):
    """
        Test put request when db error occurs
    """
    #test when ValueErorr occured
    valid = _get_song_json()

    # Mock the db commit
    mock_commit = mocker.patch('extensions.db.session.commit')
    # Make commit raise an exception
    mock_commit.side_effect = ValueError("Mocked exception")

    resp = client.put(f'{RESOURCE_URL}1/', json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["message"] == "Invalid input data: Mocked exception"

def test_delete_song(client):
    """
        Test delete request 
    """
    #delete song with valid id
    resp = client.delete(f'{RESOURCE_URL}2/')
    assert resp.status_code == 200

    #delete song with same id
    resp = client.delete(f'{RESOURCE_URL}2/')
    assert resp.status_code == 404

    #delete song with invalid id
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
def _get_song2_json():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "song_name": "Sample Song 3",
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
        "song_duration": 56
    }
