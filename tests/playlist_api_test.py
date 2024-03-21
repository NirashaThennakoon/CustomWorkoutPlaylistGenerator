import json
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/playlist/'

def test_get_playlist(client):
    response = client.get(f'{RESOURCE_URL}2/')
    print(response.data)
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) != 0

def test_post_playlist(client):
        valid = _get_playlist_post_json()

        # test with wrong content type
        resp = client.post(RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        # test with valid and see that it exists afterward
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 201
    

        # remove workout_name field for 400
        valid.pop("workout_ids")
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 400

def test_put_playlist(client):
        valid = _get_playlist_json()

        # test with wrong content type
        resp = client.put(f'{RESOURCE_URL}2/', data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # test withoyt data
        resp = client.put(f'{RESOURCE_URL}2/', data = None, headers=Headers({"Content-Type": "application/json"}))
        assert resp.status_code== 400

        #test with wrong id
        resp = client.put(f'{RESOURCE_URL}id/', json=valid)
        assert resp.status_code == 404
        
        # test with not avaliable id
        resp = client.put(f'{RESOURCE_URL}10000/', json=valid)
        assert resp.status_code == 404

        # test with valid
        resp = client.put(f'{RESOURCE_URL}1/', json=valid)
        assert resp.status_code == 204
        
        # remove field
        valid.pop("playlist_name")
        resp = client.put(f'{RESOURCE_URL}2/', json=valid)
        assert resp.status_code == 204

def test_delete_playlist(client):
        resp = client.delete(f'{RESOURCE_URL}3/')
        assert resp.status_code == 204
        resp = client.delete(f'{RESOURCE_URL}3/')
        assert resp.status_code == 404
        resp = client.delete(f'{RESOURCE_URL}id/')
        assert resp.status_code == 404

def _get_playlist_json():
    """
    Creates a valid playlist JSON object to be used for PUT and POST tests.
    """
    return {
        "playlist_name": "Sample Playlist 1",
        "song_list": [1,2,3]
    }

def _get_playlist_post_json():
    """
    Creates a valid playlist JSON object to be used for PUT and POST tests.
    """
    return {
        "playlist_name": "test-workout-plan-1 Playlist",
        "workout_ids": [1, 2 ,3, 4, 5, 6]
    }
