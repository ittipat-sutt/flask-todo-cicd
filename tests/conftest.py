import pytest
from app import create_app, db

@pytest.fixture
def app():
    """Create and configure a new app instance for each test."""
    app = create_app('testing')
    with app.app_context():
        db.create_all()
    yield app
    with app.app_context():
        db.drop_all()

@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()
