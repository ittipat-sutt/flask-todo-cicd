import pytest
from unittest.mock import patch
from sqlalchemy.exc import SQLAlchemyError
from app import create_app, db
from app.models import Todo
 
# =======================
# Fixtures
# =======================
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
 
 
# =========================================================
# 1. TestAppFactory — ทดสอบการสร้างแอปและ error handler
# =========================================================
class TestAppFactory:
    """Test application factory and configuration"""
    
    def test_app_creation(self, app):
        assert app is not None
        assert app.config['TESTING'] is True
    
    def test_root_endpoint(self, client):
        response = client.get('/')
        assert response.status_code == 200
        data = response.get_json()
        assert 'message' in data
        assert 'version' in data
        assert 'endpoints' in data
    
    def test_404_error_handler(self, client):
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
        data = response.get_json()
        assert data['success'] is False
        assert 'error' in data
    
    def test_exception_handler(self, app):
        # ปิด TESTING mode ชั่วคราว
        app.config['TESTING'] = False
        
        @app.route('/test-error')
        def trigger_error():
            raise Exception('Test error')
        
        with app.test_client() as test_client:
            response = test_client.get('/test-error')
            assert response.status_code == 500
            assert 'Internal server error' in response.get_json()['error']
        
        app.config['TESTING'] = True
 
 
# =========================================================
# 2. TestHealthCheck — ทดสอบ endpoint /api/health
# =========================================================
class TestHealthCheck:
    def test_health_endpoint_success(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'
        assert data['database'] == 'connected'
    
    @patch('app.routes.db.session.execute')
    def test_health_endpoint_database_error(self, mock_execute, client):
        mock_execute.side_effect = Exception('Database connection failed')
        response = client.get('/api/health')
        assert response.status_code == 503
        data = response.get_json()
        assert data['status'] == 'unhealthy'
        assert data['database'] == 'disconnected'
        assert 'error' in data
 
 
# =========================================================
# 3. TestTodoModel — ทดสอบ Model Layer
# =========================================================
class TestTodoModel:
    def test_todo_to_dict(self, app):
        with app.app_context():
            todo = Todo(title='Test Todo', description='Test Description')
            db.session.add(todo)
            db.session.commit()
            todo_dict = todo.to_dict()
            assert todo_dict['title'] == 'Test Todo'
            assert todo_dict['description'] == 'Test Description'
            assert todo_dict['completed'] is False
            assert 'id' in todo_dict
            assert 'created_at' in todo_dict
            assert 'updated_at' in todo_dict
    
    def test_todo_repr(self, app):
        with app.app_context():
            todo = Todo(title='Test Todo')
            db.session.add(todo)
            db.session.commit()
            repr_str = repr(todo)
            assert 'Todo' in repr_str
            assert 'Test Todo' in repr_str
 
 
# =========================================================
# 4. TestTodoAPI — ทดสอบ CRUD API ครบทุกกรณี
# =========================================================
class TestTodoAPI:
    def test_get_empty_todos(self, client):
        response = client.get('/api/todos')
        assert response.status_code == 200
        data = response.get_json()
        assert data['success'] is True
        assert data['count'] == 0
        assert data['data'] == []
    
    def test_create_todo_with_full_data(self, client):
        todo_data = {'title': 'Test Todo', 'description': 'This is a test todo'}
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo'
        assert data['data']['description'] == 'This is a test todo'
    
    def test_create_todo_with_title_only(self, client):
        todo_data = {'title': 'Test Todo Only Title'}
        response = client.post('/api/todos', json=todo_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data['data']['description'] == ''
    
    def test_create_todo_without_title(self, client):
        response = client.post('/api/todos', json={})
        assert response.status_code == 400
        data = response.get_json()
        assert data['success'] is False
        assert 'Title is required' in data['error']
    
    @patch('app.routes.db.session.commit')
    def test_create_todo_database_error(self, mock_commit, client):
        mock_commit.side_effect = SQLAlchemyError('Database error')
        response = client.post('/api/todos', json={'title': 'Test'})
        assert response.status_code == 500
        assert response.get_json()['success'] is False
    
    def test_get_todo_by_id(self, client, app):
        with app.app_context():
            todo = Todo(title='Test Todo', description='Test Description')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        response = client.get(f'/api/todos/{todo_id}')
        data = response.get_json()
        assert response.status_code == 200
        assert data['success'] is True
        assert data['data']['title'] == 'Test Todo'
    
    def test_get_nonexistent_todo(self, client):
        response = client.get('/api/todos/9999')
        assert response.status_code == 404
        data = response.get_json()
        assert 'not found' in data['error'].lower()
    
    def test_update_todo_title(self, client, app):
        with app.app_context():
            todo = Todo(title='Original Title')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        response = client.put(f'/api/todos/{todo_id}', json={'title': 'Updated Title'})
        assert response.status_code == 200
        assert response.get_json()['data']['title'] == 'Updated Title'
    
    def test_delete_todo(self, client, app):
        with app.app_context():
            todo = Todo(title='To Be Deleted')
            db.session.add(todo)
            db.session.commit()
            todo_id = todo.id
        response = client.delete(f'/api/todos/{todo_id}')
        assert response.status_code == 200
        assert response.get_json()['success'] is True
        # Verify deleted
        response = client.get(f'/api/todos/{todo_id}')
        assert response.status_code == 404
 
 
# =========================================================
# 5. TestIntegration — ทดสอบการทำงานจริงแบบครบวงจร
# =========================================================
class TestIntegration:
    def test_complete_todo_lifecycle(self, client):
        # Create
        create_response = client.post('/api/todos', json={
            'title': 'Integration Test Todo',
            'description': 'Testing full lifecycle'
        })
        assert create_response.status_code == 201
        todo_id = create_response.get_json()['data']['id']
        
        # Read
        read_response = client.get(f'/api/todos/{todo_id}')
        assert read_response.status_code == 200
        assert read_response.get_json()['data']['title'] == 'Integration Test Todo'
        
        # Update
        update_response = client.put(f'/api/todos/{todo_id}', json={
            'title': 'Updated Integration Test',
            'completed': True
        })
        updated_data = update_response.get_json()['data']
        assert updated_data['title'] == 'Updated Integration Test'
        assert updated_data['completed'] is True
        
        # Delete
        delete_response = client.delete(f'/api/todos/{todo_id}')
        assert delete_response.status_code == 200
        
        # Verify deletion
        verify_response = client.get(f'/api/todos/{todo_id}')
        assert verify_response.status_code == 404