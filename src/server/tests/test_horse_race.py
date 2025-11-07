import json
import pytest
from flask_login import login_user

def test_horse_race_start(client, test_user):
    """Test starting a horse race"""
    login_user(test_user)
    response = client.post('/api/caballos/apostar', json={
        'cantidad': 100,
        'caballo_apostado': 1,
        'resultado': 'ganada',
        'ganancia': 150
    })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'nuevo_balance' in data

def test_horse_race_result(client, test_user):
    """Test getting race results"""
    login_user(test_user)
    # The API provides apostar which can include caballo_ganador info
    response = client.post('/api/caballos/apostar', json={
        'cantidad': 100,
        'caballo_apostado': 1,
        'caballo_ganador': 1,
        'resultado': 'ganada',
        'ganancia': 150
    })

    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'caballo_ganador' in data
    assert 'nuevo_balance' in data

def test_horse_race_invalid_horse(client, test_user):
    """Test betting on invalid horse number"""
    login_user(test_user)
    response = client.post('/api/caballos/apostar', json={
        'cantidad': 100,
        'caballo_apostado': 10,  # Invalid horse number
        'resultado': 'perdida',
        'ganancia': 0
    })

    assert response.status_code == 400