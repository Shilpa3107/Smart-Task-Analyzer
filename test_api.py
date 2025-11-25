import pytest
from fastapi.testclient import TestClient
from main import app
from datetime import date, timedelta

client = TestClient(app)

def test_analyze_tasks():
    # Test data
    today = date.today()
    tomorrow = today + timedelta(days=1)
    next_week = today + timedelta(weeks=1)
    
    task1 = {
        "title": "Urgent and important",
        "due_date": tomorrow.isoformat(),
        "estimated_hours": 2,
        "importance": 9,
        "dependencies": []
    }
    
    task2 = {
        "title": "Low priority",
        "due_date": next_week.isoformat(),
        "estimated_hours": 8,
        "importance": 3,
        "dependencies": []
    }
    
    task3 = {
        "title": "Blocked task",
        "due_date": tomorrow.isoformat(),
        "estimated_hours": 4,
        "importance": 7,
        "dependencies": ["task1"]
    }
    
    # Test with default weights
    response = client.post("/api/tasks/analyze/", json={"tasks": [task1, task2, task3]})
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 3
    
    # The urgent and important task should have the highest score
    assert data["tasks"][0]["title"] == "Urgent and important"
    
    # Test with custom weights (favoring importance)
    custom_weights = {
        "urgency": 0.2,
        "importance": 0.7,
        "effort": 0.05,
        "dependencies": 0.05
    }
    
    response = client.post("/api/tasks/analyze/", json={
        "tasks": [task1, task2, task3],
        "weights": custom_weights
    })
    assert response.status_code == 200
    
    # Test with circular dependencies
    circular_task1 = {
        "id": "task1",
        "title": "Circular 1",
        "due_date": tomorrow.isoformat(),
        "estimated_hours": 2,
        "importance": 5,
        "dependencies": ["task2"]
    }
    
    circular_task2 = {
        "id": "task2",
        "title": "Circular 2",
        "due_date": tomorrow.isoformat(),
        "estimated_hours": 2,
        "importance": 5,
        "dependencies": ["task1"]
    }
    
    response = client.post("/api/tasks/analyze/", json={"tasks": [circular_task1, circular_task2]})
    assert response.status_code == 400
    assert "circular dependency" in response.text.lower()
    
    # Test with non-existent dependency
    invalid_dep_task = {
        "title": "Invalid dep",
        "due_date": tomorrow.isoformat(),
        "estimated_hours": 2,
        "importance": 5,
        "dependencies": ["non-existent-task"]
    }
    
    response = client.post("/api/tasks/analyze/", json={"tasks": [invalid_dep_task]})
    assert response.status_code == 400
    assert "non-existent task" in response.text.lower()

def test_suggest_tasks():
    # This is a simple test since the endpoint is a placeholder
    response = client.get("/api/tasks/suggest/")
    assert response.status_code == 200
    assert "message" in response.json()
