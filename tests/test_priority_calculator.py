import pytest
from datetime import date, timedelta
from main import PriorityCalculator
from database import TaskDB, get_db, init_db
from sqlalchemy.orm import Session

# Test data
today = date.today()
tomorrow = today + timedelta(days=1)
yesterday = today - timedelta(days=1)

# Fixture for database session
@pytest.fixture(scope="module")
def db_session():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Use in-memory SQLite for testing
    TEST_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(TEST_DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    from database import Base
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

# Test cases for PriorityCalculator
def test_priority_calculation_high_importance():
    """Test that high importance tasks get higher scores"""
    calculator = PriorityCalculator()
    
    # High importance task
    high_importance_task = TaskDB(
        id="1",
        title="Important Task",
        due_date=tomorrow,
        estimated_hours=4,
        importance=9  # High importance
    )
    
    # Lower importance task
    low_importance_task = TaskDB(
        id="2",
        title="Less Important Task",
        due_date=tomorrow,
        estimated_hours=4,
        importance=3  # Low importance
    )
    
    tasks = {task.id: task for task in [high_importance_task, low_importance_task]}
    
    # Calculate scores
    high_score = calculator.calculate_score(high_importance_task, tasks)
    low_score = calculator.calculate_score(low_importance_task, tasks)
    
    # High importance task should have a higher score
    assert high_score > low_score
    assert high_importance_task.importance > low_importance_task.importance

def test_priority_calculation_urgency():
    """Test that urgent tasks get higher scores"""
    calculator = PriorityCalculator()
    
    # Task due today
    urgent_task = TaskDB(
        id="3",
        title="Urgent Task",
        due_date=today,
        estimated_hours=4,
        importance=5
    )
    
    # Task due in a week
    non_urgent_task = TaskDB(
        id="4",
        title="Not Urgent Task",
        due_date=today + timedelta(days=7),
        estimated_hours=4,
        importance=5
    )
    
    tasks = {task.id: task for task in [urgent_task, non_urgent_task]}
    
    # Calculate scores
    urgent_score = calculator.calculate_score(urgent_task, tasks)
    non_urgent_score = calculator.calculate_score(non_urgent_task, tasks)
    
    # Urgent task should have a higher score
    assert urgent_score > non_urgent_score

def test_priority_calculation_dependencies():
    """Test that tasks with dependencies get appropriate scores"""
    calculator = PriorityCalculator()
    
    # Create tasks with dependencies
    task_a = TaskDB(
        id="5",
        title="Task A",
        due_date=tomorrow,
        estimated_hours=2,
        importance=5
    )
    
    task_b = TaskDB(
        id="6",
        title="Task B",
        due_date=tomorrow,
        estimated_hours=2,
        importance=5
    )
    
    # Task C depends on A and B
    task_c = TaskDB(
        id="7",
        title="Task C (depends on A and B)",
        due_date=tomorrow,
        estimated_hours=2,
        importance=5
    )
    
    # Set up dependencies
    task_c.dependencies = [task_a, task_b]
    
    tasks = {task.id: task for task in [task_a, task_b, task_c]}
    
    # Calculate scores
    score_a = calculator.calculate_score(task_a, tasks)
    score_b = calculator.calculate_score(task_b, tasks)
    score_c = calculator.calculate_score(task_c, tasks)
    
    # Tasks that are depended upon should have higher scores
    assert score_a > score_c
    assert score_b > score_c
    
    # Test explanation includes dependency information
    explanation = calculator.generate_explanation(task_a, tasks)
    assert "Blocks 1 other task" in explanation

def test_priority_calculation_past_due():
    """Test that past due tasks get high urgency scores"""
    calculator = PriorityCalculator()
    
    # Past due task
    past_due_task = TaskDB(
        id="8",
        title="Past Due Task",
        due_date=yesterday,
        estimated_hours=2,
        importance=3  # Even with low importance, should be high priority
    )
    
    tasks = {"8": past_due_task}
    
    # Calculate score
    score = calculator.calculate_score(past_due_task, tasks)
    
    # Past due tasks should have high scores
    assert score > 70  # Should be in the high priority range
    
    # Test explanation mentions it's past due
    explanation = calculator.generate_explanation(past_due_task, tasks)
    assert "Past due by 1 days" in explanation
