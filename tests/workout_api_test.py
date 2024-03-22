import json
from werkzeug.datastructures import Headers

RESOURCE_URL = '/api/workout'    

def test_get_workout(client):
    response = client.get("/api/workout/1")
    assert response.status_code == 200

    data = json.loads(response.data)
    assert len(data) == 1

def test_get_workouts(client):
    response = client.get(RESOURCE_URL)
    assert response.status_code == 200

def test_post_workout(client):
        valid = _get_workout_json()
        invalidIntensityJson = _get_invalid_workout_json()

        # test with wrong content type
        resp = client.post(RESOURCE_URL, data="notjson")
        assert resp.status_code in (400, 415)

        #test with wrong intensity
        resp = client.post(RESOURCE_URL, json=invalidIntensityJson)
        assert resp.status_code == 400

        # test with valid and see that it exists afterward
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 201

        # invalid duration type
        valid["duration" ] = 10
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        # remove workout_name field for 400
        valid.pop("workout_name")
        resp = client.post(RESOURCE_URL, json=valid)
        assert resp.status_code == 400

def test_put_workout(client):
        valid = _get_workout_json()
        invalidJson = _get_invalid_workout_json()

        # test with wrong content type
        resp = client.put(f'{RESOURCE_URL}/1', data="notjson", headers=Headers({"Content-Type": "text"}))
        assert resp.status_code in (400, 415)

        # test with wrong content type
        resp = client.put(f'{RESOURCE_URL}/1', data = None, headers=Headers({"Content-Type": "application/json"}))
        assert resp.status_code == 400

        #test with wrong id
        resp = client.put(f'{RESOURCE_URL}/id', json=valid)
        assert resp.status_code == 404
        
        # test with not avaliable id
        resp = client.put(f'{RESOURCE_URL}/10000', json=valid)
        assert resp.status_code == 404
        
        # test with valid
        resp = client.put(f'{RESOURCE_URL}/1', json=valid)
        assert resp.status_code == 200
        
        # remove field
        valid.pop("workout_name")
        resp = client.put(f'{RESOURCE_URL}/1', json=valid)
        assert resp.status_code == 200

        #invalid intensity
        # resp = client.put(f'{RESOURCE_URL}/1', json=invalidJson)
        # assert resp.status_code == 400

def test_delete_workout(client):
        resp = client.delete(f'{RESOURCE_URL}/2')
        assert resp.status_code == 200
        resp = client.delete(f'{RESOURCE_URL}/2')
        assert resp.status_code == 404
        resp = client.delete(f'{RESOURCE_URL}/2')
        assert resp.status_code == 404

def _get_workout_json():
    """
    Creates a valid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
        "workout_name": "Sample Workout",
        "duration": 30.0,
        "workout_intensity": "slow",
        "equipment": "Dumbbells",
        "workout_type": "Strength"
    }

def _get_invalid_workout_json():
    """
    Creates an invalid workout JSON object to be used for PUT and POST tests.
    """
    
    return {
        "workout_name": "Sample Workout",
        "duration": 30.0,
        "workout_intensity": "invalid",
        "equipment": "Dumbbells",
        "workout_type": "Strength"
    }
