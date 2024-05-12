"""
    This module is for test funstionalities of Song reaource
"""
import json
from jsonschema import validate
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
    _check_namespace(client, data)
    _check_control_get_method("collection", client, data)
    _check_control_put_method("edit", client, data)
    _check_control_delete_method("delete", client, data)
    assert data['song_id'] == 1
    assert data["song_name"] == "test-song-1"


def test_get_all_songs(client):
    """
        Test get all request 
    """
    #get all songs
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data['song list']) == 5

def test_get_all_playlists_song_belongs(client):
    """
        Test get all request 
    """
    #get all songs
    response = client.get('api/allSong/3')
    assert response.status_code == 200

    data = json.loads(response.data)
    print(data)
    assert len(data['Playlists']) == 2

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
    assert data["@error"]["@message"] == "Song already exists"

    #send non-float for duration of song
    resp = client.post(RESOURCE_URL, json=invalid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Song duration must be a float"

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
    assert resp.status_code == 500

    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Internal Server Error"

def test_put_song(client):
    """
        Test put request 
    """
    valid = _get_song_json()

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}3/', data="notjson",
                        headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test with none
    resp = client.put(f'{RESOURCE_URL}3/', json={})
    assert resp.status_code== 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid JSON document"
    # test with not avaliable id
    resp = client.put(f'{RESOURCE_URL}10000/', json=valid)
    assert resp.status_code == 404
    # test with valid
    resp = client.put(f'{RESOURCE_URL}5/', json=valid)
    assert resp.status_code == 204
    data = json.loads(resp.data)
    assert data["message"] == "Song updated successfully"
    # remove field
    valid.pop("song_name")
    resp = client.put(f'{RESOURCE_URL}3/', json=valid)
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

    resp = client.put(f'{RESOURCE_URL}3/', json=valid)
    assert resp.status_code == 400

    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid input data"

def test_delete_song(client):
    """
        Test delete request 
    """
    #delete song with valid id
    resp = client.delete(f'{RESOURCE_URL}2/')
    assert resp.status_code == 204

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

def _get_song3_json():
    """
    Creates a valid song JSON object to be used for PUT and POST tests.
    """
    return {
        "song_name": "Sample Song 4",
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

def _check_namespace(client, response):
    """
    Checks that the "custWorkoutPlaylistGen" namespace is found from the response body, and
    that its "name" attribute is a URL that can be accessed.
    """

    ns_href = response["@namespaces"]["custWorkoutPlaylistGen"]["name"]
    print(ns_href)
    resp = client.get(ns_href)
    assert resp.status_code == 200

def _check_control_get_method(ctrl, client, obj):
    """
    Checks a GET type control from a JSON object be it root document or an item
    in a collection. Also checks that the URL of the control can be accessed.
    """

    href = obj["@controls"][ctrl]["href"]
    resp = client.get(href)
    print(href)
    assert resp.status_code == 200

def _check_control_delete_method(ctrl, client, obj):
    """
    Checks a DELETE type control from a JSON object be it root document or an
    item in a collection. Checks the contrl's method in addition to its "href".
    Also checks that using the control results in the correct status code of 204.
    """

    href = obj["@controls"][ctrl]["href"]
    method = obj["@controls"][ctrl]["method"].lower()
    assert method == "delete"
    resp = client.delete(href)
    assert resp.status_code == 200

def _check_control_put_method(ctrl, client, obj):
    """
    Checks a PUT type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 204.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "put"
    assert encoding == "json"
    body = _get_song_json()
    body["song_name"] = obj["song_name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 200
