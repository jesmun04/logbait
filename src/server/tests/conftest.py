import os
import sys
import pytest
from app import app as flask_app
from models import db, User

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

@pytest.fixture(scope='session')
def app():
    # Configure the Flask app for testing
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for testing
        'SERVER_NAME': 'localhost.localdomain'  # Required for url_for to work
    })
    
    with flask_app.app_context():
        # Initialize database
        db.create_all()
        
        # Register all blueprints
        from endpoints import register_blueprints
        register_blueprints(flask_app)
        
        yield flask_app
        
        # Clean up database
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def test_user(app):
    with app.app_context():
        # Clean up any existing test user first
        from models import Apuesta, Estadistica
        existing_user = User.query.filter_by(email="test@test.com").first()
        if existing_user is not None:
            Apuesta.query.filter_by(user_id=existing_user.id).delete()
            Estadistica.query.filter_by(user_id=existing_user.id).delete()
            db.session.delete(existing_user)
            db.session.commit()
        
        # Create new test user
        user = User(
            username="test_user",
            email="test@test.com"
        )
        user.set_password("password123")
        user.balance = 1000  # Initial balance for testing
        db.session.add(user)
        db.session.commit()
        
        # Get the user ID before yielding
        user_id = user.id
        
        yield user
        
        # Clean up user after test
        user = User.query.get(user_id)
        if user is not None:
            Apuesta.query.filter_by(user_id=user.id).delete()
            Estadistica.query.filter_by(user_id=user.id).delete()
            db.session.delete(user)
            db.session.commit()