import pytest
import httpx
import uvicorn
import threading
import time
from datetime import date, timedelta

# Start the FastAPI server in a separate thread
def start_server():
    uvicorn.run("main:app", host="127.0.0.1", port=8000, log_level="info")

@pytest.fixture(scope="module")
def server():
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(2)  # Give the server time to start
    yield
    # No need to explicitly stop the server as it's a daemon thread

@pytest.fixture
def client():
    return httpx.Client(base_url="http://localhost:8000")

def test_analyze_tasks_priority_scoring(client):
    task1 = {
        "title": "High priority task",
        "due_date": (date.today() + timedelta(days=1)).isoformat(),
        "estimated_hours": 2,
        "importance": 9,
        "dependencies": []
    }
    
    task2 = {
        "title": "Medium priority task",
        "due_date": (date.today() + timedelta(weeks=1)).isoformat(),
        "estimated_hours": 4,
        "importance": 5,
        "dependencies": []
    }
    
    response = client.post("/api/tasks/analyze/", json={
        "tasks": [task1, task2],
        "weights": {
            "urgency": 0.4,
            "importance": 0.3,
            "effort": 0.2,
            "dependencies": 0.1
        }
    })
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["tasks"]) == 2
    # High priority task should have higher score
    assert data["tasks"][0]["score"] > data["tasks"][1]["score"]

def test_analyze_tasks_with_weights(client):
    # Test data with different priorities
    tasks = [
        {
            "title": "High importance, urgent task",
            "due_date": (date.today() + timedelta(days=1)).isoformat(),
            "estimated_hours": 2,
            "importance": 9,
            "dependencies": []
        },
        {
            "title": "Low importance, not urgent task",
            "due_date": (date.today() + timedelta(weeks=2)).isoformat(),
            "estimated_hours": 4,
            "importance": 3,
            "dependencies": []
        }
    ]

    # Test with default weights
    response = client.post("/api/tasks/analyze/", json={
        "tasks": tasks,
        "weights": {
            "urgency": 0.4,
            "importance": 0.4,
            "effort": 0.1,
            "dependencies": 0.1
        }
    })
    
    assert response.status_code == 200, f"Expected status code 200, but got {response.status_code}. Response: {response.text}"
    
    data = response.json()
    assert "tasks" in data
    assert len(data["tasks"]) == 2
    
    # The first task should have a higher score due to higher importance and urgency
    assert data["tasks"][0]["score"] > data["tasks"][1]["score"], \
        f"Expected first task to have higher score, but got: {data['tasks'][0]['score']} vs {data['tasks'][1]['score']}"
    
    # Verify all tasks have the required fields
    for task in data["tasks"]:
        assert "id" in task
        assert "title" in task
        assert "score" in task
        assert isinstance(task["score"], (int, float))

def test_get_task_suggestions(client):
    # First, add some test tasks
    tasks = [
        {
            "title": "Urgent task",
            "due_date": date.today().isoformat(),
            "estimated_hours": 2,
            "importance": 8,
            "dependencies": []
        },
        {
            "title": "Important but not urgent",
            "due_date": (date.today() + timedelta(weeks=1)).isoformat(),
            "estimated_hours": 4,
            "importance": 9,
            "dependencies": []
        }
    ]
    
    # Add tasks
    for task in tasks:
        response = client.post("/api/tasks/", json=task)
        assert response.status_code in [200, 201]
    
    # Get suggestions
    response = client.get("/api/tasks/suggest/")
    assert response.status_code == 200
    suggestions = response.json()
    assert isinstance(suggestions, list)
    # Should return at most 3 suggestions
    assert len(suggestions) <= 3
    # Should return at least one suggestion if there are tasks
    if tasks:
        assert len(suggestions) > 0