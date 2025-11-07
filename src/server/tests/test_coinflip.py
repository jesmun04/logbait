import json
import pytest
from flask_login import login_user

def test_coinflip_bet(client, test_user):
    """Test betting on coinflip"""
    login_user(test_user)
    initial_balance = test_user.balance
    
    response = client.post('/api/coinflip/apostar', json={
        'eleccion': 'cara',
        'cantidad': 100,
        'resultado_moneda': 'cruz'
    })
    
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'resultado' in data
    # API returns 'ganada' or 'perdida' as resultado
    assert data['resultado'] in ['ganada', 'perdida']
    assert 'ganancia' in data

def test_coinflip_invalid_choice(client, test_user):
    """Test invalid choice in coinflip"""
    login_user(test_user)
    
    response = client.post('/api/coinflip/apostar', json={
        'eleccion': 'invalido',
        'cantidad': 100,
        'resultado_moneda': 'cara'
    })
    
    assert response.status_code == 400

def test_coinflip_invalid_amount(client, test_user):
    """Test invalid bet amount in coinflip"""
    login_user(test_user)
    
    response = client.post('/api/coinflip/apostar', json={
        'eleccion': 'cara',
        'cantidad': -100,
        'resultado_moneda': 'cara'
    })
    
    assert response.status_code == 400