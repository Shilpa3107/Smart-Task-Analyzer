from datetime import date, timedelta
from main import PriorityCalculator
from database import TaskDB, SessionLocal

def test_priority_calculation():
    # Initialize the calculator
    calculator = PriorityCalculator()
    db = SessionLocal()
    
    try:
        # Create test tasks
        today = date.today()
        
        # Task 1: High importance, due soon
        task1 = TaskDB(
            id="test1",
            title="High importance task",
            due_date=today + timedelta(days=1),
            estimated_hours=2,
            importance=9
        )
        
        # Task 2: Low importance, not urgent
        task2 = TaskDB(
            id="test2",
            title="Low importance task",
            due_date=today + timedelta(days=14),
            estimated_hours=1,
            importance=3
        )
        
        # Calculate priorities
        task1_score = calculator.calculate_score(task1, db)
        task2_score = calculator.calculate_score(task2, db)
        
        print(f"Task 1 ('{task1.title}') score: {task1_score}")
        print(f"Task 2 ('{task2.title}') score: {task2_score}")
        
        # Assert that high importance task has higher score
        assert task1_score > task2_score, "High importance task should have higher score"
        print("✓ Test passed: High importance task has higher score")
        
    finally:
        db.close()

if __name__ == "__main__":
    test_priority_calculation()
