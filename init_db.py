from database import SessionLocal, engine, init_db
from database import TaskDB
from datetime import date, timedelta

def init_sample_data():
    db = SessionLocal()
    
    # Clear existing data
    db.query(TaskDB).delete()
    db.commit()
    
    # Create sample tasks
    today = date.today()
    
    # Task 1: High importance, due soon
    task1 = TaskDB(
        id="1",
        title="Complete project presentation",
        due_date=today + timedelta(days=2),
        estimated_hours=4,
        importance=9
    )
    
    # Task 2: Medium importance, quick task
    task2 = TaskDB(
        id="2",
        title="Reply to client emails",
        due_date=today + timedelta(days=3),
        estimated_hours=1,
        importance=6
    )
    
    # Task 3: Low importance, not urgent
    task3 = TaskDB(
        id="3",
        title="Update documentation",
        due_date=today + timedelta(days=14),
        estimated_hours=3,
        importance=3
    )
    
    # Task 4: Depends on task 1
    task4 = TaskDB(
        id="4",
        title="Submit final report",
        due_date=today + timedelta(days=3),
        estimated_hours=2,
        importance=8
    )
    task4.dependencies.append(task1)  # Depends on task 1
    
    # Add all tasks to the session
    db.add_all([task1, task2, task3, task4])
    db.commit()
    
    print("Sample data initialized successfully!")
    print(f"Added {db.query(TaskDB).count()} tasks to the database.")

if __name__ == "__main__":
    # Initialize the database
    init_db()
    
    # Add sample data
    init_sample_data()
