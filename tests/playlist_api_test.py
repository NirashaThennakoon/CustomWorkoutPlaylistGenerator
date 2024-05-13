"""
    This module is to test functionalities of playlist resource
"""
import json
from jsonschema import validate
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/playlist/'

def test_get_playlist(client):
    """
        test get request of playlist
    """
    response = client.get(f'{RESOURCE_URL}2/')
    assert response.status_code == 200

    json_data = json.loads(response.data)
    _check_namespace(client, json_data)
    _check_control_get_method("item", client, json_data)
    _check_control_put_method("edit", client, json_data)
    _check_control_delete_method("delete", client, json_data)
    assert json_data['playlist_id'] == 2
    # Ensure there are only three keys in the JSON data
    assert 'playlist_duration' in json_data
    assert 'playlist_id' in json_data
    assert 'songs_list' in json_data

def test_post_playlist(client):
    """
        test post request of playlist
    """
    valid = _get_playlist_post_json()

    # test with wrong content type
    resp = client.post(RESOURCE_URL, data="notjson")
    assert resp.status_code in (400, 415)

    # test with valid and see that it exists afterward
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 201
    data = json.loads(resp.data)
    assert data["message"] == "Playlist created successfully", "playlist_id : 4"
    # remove workout_name field for 400
    valid.pop("workout_ids")
    resp = client.post(RESOURCE_URL, json=valid)
    assert resp.status_code == 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "Invalid input data on CreatePlayList"

def test_put_playlist(client):
    """
        test put request of playlist
    """
    valid = _get_playlist_json()

    # test with wrong content type
    resp = client.put(f'{RESOURCE_URL}5/', data="notjson",
                      headers=Headers({"Content-Type": "text"}))
    assert resp.status_code in (400, 415)

    # test withoyt data
    resp = client.put(f'{RESOURCE_URL}5/', json = {})
    assert resp.status_code== 400
    data = json.loads(resp.data)
    assert data["@error"]["@message"] == "No input data provided"
    # test without passing playllist id in url
    playlist = None
    resp = client.put(f'{RESOURCE_URL}{playlist}/', json = valid)
    assert resp.status_code== 404
    #test with wrong id
    resp = client.put(f'{RESOURCE_URL}id/', json=valid)
    assert resp.status_code == 404
    # test with not avaliable id
    resp = client.put(f'{RESOURCE_URL}10000/', json=valid)
    assert resp.status_code == 404

    # test with valid
    resp = client.put(f'{RESOURCE_URL}5/', json=valid)
    assert resp.status_code == 204
    # remove field
    valid.pop("playlist_name")
    resp = client.put(f'{RESOURCE_URL}5/', json=valid)
    assert resp.status_code == 400

def test_delete_playlist(client):
    """
        test delete request of playlist
    """
    #delete playlist with a valid id
    resp = client.delete(f'{RESOURCE_URL}3/')
    assert resp.status_code == 204
    #delete playlist with same id
    resp = client.delete(f'{RESOURCE_URL}3/')
    assert resp.status_code == 404
    #delete playlist with invalid id
    resp = client.delete(f'{RESOURCE_URL}id/')
    assert resp.status_code == 404

def _get_playlist_json():
    """
    Creates a valid playlist JSON object to be used for PUT and POST tests.
    """
    return {
        "playlist_name": "Sample Playlist 1",
        "song_list": [1,2,3],
        "playlist_duration": 89.0
    }

def _get_playlist_post_json():
    """
    Creates a valid playlist JSON object to be used for PUT and POST tests.
    """
    return {
        "playlist_name": "test-workout-plan-4 Playlist",
        "workout_ids": [1, 2 ,3, 4, 5, 6]
    }

def _get_playlist_post_json_with_controls():
    """
    Creates a valid playlist JSON object to be used for PUT and POST tests.
    """
    return {
        "playlist_name": "test-workout-plan-2 Playlist",
        "workout_ids": [1, 2 ,3, 4, 5, 6],
        "playlist_duration": 38.0
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
    assert resp.status_code == 204

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
    body = _get_playlist_json()
    print(obj)
    body["playlist_name"] = obj["playlist_name"]
    validate(body, schema)
    resp = client.put(href, json=body)
    assert resp.status_code == 204

def _check_control_post_method(ctrl, client, obj):
    """
    Checks a POST type control from a JSON object be it root document or an item
    in a collection. In addition to checking the "href" attribute, also checks
    that method, encoding and schema can be found from the control. Also
    validates a valid sensor against the schema of the control to ensure that
    they match. Finally checks that using the control results in the correct
    status code of 201.
    """

    ctrl_obj = obj["@controls"][ctrl]
    href = ctrl_obj["href"]
    method = ctrl_obj["method"].lower()
    encoding = ctrl_obj["encoding"].lower()
    schema = ctrl_obj["schema"]
    assert method == "post"
    assert encoding == "json"
    body = _get_playlist_post_json_with_controls()
    validate(body, schema)
    print(href)
    resp = client.post(href, json=body)
    assert resp.status_code == 201
