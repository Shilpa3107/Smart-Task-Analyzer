import sys
import json
import requests
from datetime import date, timedelta

# Base URL for the API
BASE_URL = "http://127.0.0.1:8000/api"

def print_test_header(test_name):
    print(f"\n{'='*50}")
    print(f"TEST: {test_name}")
    print("="*50)

def test_create_task(title, due_date, importance, estimated_hours, dependencies=None):
    """Test creating a new task"""
    if dependencies is None:
        dependencies = []
        
    task_data = {
        "title": title,
        "due_date": due_date.isoformat(),
        "importance": importance,
        "estimated_hours": estimated_hours,
        "dependencies": dependencies
    }
    
    print(f"Creating task: {title}")
    response = requests.post(f"{BASE_URL}/tasks/", json=task_data)
    
    if response.status_code == 200:
        task = response.json()
        print(f"[OK] Task created successfully (ID: {task['id']})")
        return task
    else:
        print(f"[X] Failed to create task: {response.text}")
        return None

def test_get_tasks():
    """Test getting all tasks"""
    print("Fetching all tasks...")
    response = requests.get(f"{BASE_URL}/tasks/")
    
    if response.status_code == 200:
        tasks = response.json()
        print(f"[OK] Retrieved {len(tasks)} tasks")
        for task in tasks:
            print(f"  - {task['title']} (ID: {task['id']}, Score: {task.get('score', 'N/A')})")
        return tasks
    else:
        print(f"[X] Failed to fetch tasks: {response.text}")
        return []

def test_get_suggestions():
    """Test getting task suggestions"""
    print("\nGetting task suggestions...")
    response = requests.get(f"{BASE_URL}/tasks/suggest/")
    
    if response.status_code == 200:
        suggestions = response.json()
        print(f"[OK] Retrieved {len(suggestions)} suggestions")
        for i, task in enumerate(suggestions, 1):
            print(f"  {i}. {task['title']} (Score: {task.get('score', 'N/A')})")
        return suggestions
    else:
        print(f"[X] Failed to fetch suggestions: {response.text}")
        return []

def test_complete_task(task_id, expect_success=True):
    """Test marking a task as complete"""
    print(f"\nMarking task {task_id} as complete...")
    response = requests.delete(f"{BASE_URL}/tasks/{task_id}")
    
    if expect_success:
        if response.status_code == 204:  # 204 No Content is expected for successful deletion
            print(f"[OK] Task {task_id} marked as complete")
            return True
        else:
            print(f"[X] Failed to mark task as complete: {response.status_code} - {response.text}")
            return False
    else:
        if response.status_code in (400, 404):
            print(f"[OK] Task {task_id} correctly prevented from completion: {response.text}")
            return True
        else:
            print(f"[X] Task {task_id} was unexpectedly completed: {response.status_code} - {response.text}")
            return False

def run_comprehensive_test():
    """Run a comprehensive test of all functionality"""
    print("\n" + "="*60)
    print("SMART TASK ANALYZER - COMPREHENSIVE TEST")
    print("="*60 + "\n")
    
    # Clear existing tasks
    print("Clearing existing tasks...")
    tasks = test_get_tasks()
    for task in tasks:
        test_complete_task(task['id'])
    
    # Test 1: Create tasks with different priorities and due dates
    print_test_header("1. Creating Test Tasks")
    today = date.today()
    
    # High importance, due soon
    task1 = test_create_task(
        "Prepare project presentation", 
        today + timedelta(days=1), 
        importance=9,
        estimated_hours=4
    )
    
    # Medium importance, due in a week
    task2 = test_create_task(
        "Review team's pull requests",
        today + timedelta(days=7),
        importance=6,
        estimated_hours=2
    )
    
    # Low importance, not urgent
    task3 = test_create_task(
        "Update project documentation",
        today + timedelta(days=14),
        importance=3,
        estimated_hours=3
    )
    
    # Depends on task1
    task4 = test_create_task(
        "Submit final report",
        today + timedelta(days=2),
        importance=8,
        estimated_hours=2,
        dependencies=[task1['id']] if task1 else []
    )
    
    # Test 2: Get all tasks
    print_test_header("2. Listing All Tasks")
    tasks = test_get_tasks()
    
    # Test 3: Get task suggestions
    print_test_header("3. Testing Task Suggestions")
    suggestions = test_get_suggestions()
    
    # Verify suggestions are in correct order (highest priority first)
    if len(suggestions) >= 2:
        print("\nVerifying suggestion order...")
        if suggestions[0]['score'] >= suggestions[1]['score']:
            print("[OK] Suggestions are correctly ordered by priority")
        else:
            print("[X] Suggestions are not correctly ordered by priority")
    
    # Test 4: Test task dependencies
    if task1 and task4:  # task4 depends on task1
        print_test_header("4. Testing Task Dependencies")
        print("\nAttempting to complete a task with dependencies...")
        # Try to complete task1 (which task4 depends on)
        success = test_complete_task(task1['id'], expect_success=False)
        if success:
            print("[OK] Correctly prevented completion of task with dependents")
        else:
            print("[X] Should not be able to complete a task with dependents")
    
    # Test 5: Complete tasks in correct order
    print_test_header("5. Testing Task Completion Order")
    if task4 and task1:
        # First complete task4 (which depends on task1)
        print("\nCompleting dependent tasks first...")
        success = test_complete_task(task4['id'], expect_success=True)
        
        # Then complete task1 (now that nothing depends on it)
        if success:
            print("\nNow completing the original task...")
            success = test_complete_task(task1['id'], expect_success=True)
            
            if success:
                # Verify tasks were removed
                updated_tasks = test_get_tasks()
                task_ids = [t['id'] for t in updated_tasks]
                if task1['id'] not in task_ids and task4['id'] not in task_ids:
                    print("[OK] Both tasks successfully completed in correct order")
                else:
                    print("[X] One or both tasks still appear in active tasks")
    
    print("\n" + "="*60)
    print("COMPREHENSIVE TEST COMPLETED")
    print("="*60 + "\n")

if __name__ == "__main__":
    try:
        run_comprehensive_test()
    except requests.exceptions.RequestException as e:
        print(f"\nError: Could not connect to the API. Is the server running? ({e})")
        sys.exit(1)
