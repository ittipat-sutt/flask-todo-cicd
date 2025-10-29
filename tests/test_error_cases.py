import pytest
from unittest.mock import patch
from app.models import db, Todo


@pytest.fixture
def sample_todo(app):
    """สร้าง Todo สำหรับทดสอบ"""
    with app.app_context():
        todo = Todo(title="Sample Todo")
        db.session.add(todo)
        db.session.commit()
        todo_id = todo.id  # เก็บ id ก่อน session ปิด
    return todo_id


def test_get_todo_database_error(client):
    """จำลอง error ตอน query todo"""
    with patch("app.routes.db.session.get", side_effect=Exception("DB error")):
        # ให้ pytest คาดว่ามี Exception เกิดขึ้น
        with pytest.raises(Exception):
            client.get("/api/todos/1")


def test_update_todo_database_error(client, sample_todo):
    """จำลอง commit ล้มเหลวตอน update"""
    with patch.object(db.session, "commit", side_effect=Exception("commit fail")):
        # ให้ pytest คาดว่ามี Exception เกิดขึ้น (Flask จะโยนขึ้นมา)
        with pytest.raises(Exception):
            client.put(f"/api/todos/{sample_todo}", json={"title": "Bad Commit"})


def test_delete_todo_database_error(client, sample_todo):
    """จำลอง commit ล้มเหลวตอน delete"""
    with patch.object(db.session, "commit", side_effect=Exception("commit fail")):
        # ให้ pytest คาดว่ามี Exception เกิดขึ้น
        with pytest.raises(Exception):
            client.delete(f"/api/todos/{sample_todo}")


def test_health_check_error(client):
    """จำลอง health check ล้มเหลว"""
    with patch("app.routes.db.session.execute", side_effect=Exception("DB down")):
        res = client.get("/api/health")
        data = res.get_json()
        assert res.status_code == 503
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
