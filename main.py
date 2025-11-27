from fastapi import FastAPI, HTTPException, Depends, status, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from datetime import datetime, date, timedelta
import json
from enum import Enum
import uuid
from collections import defaultdict
from sqlalchemy.orm import Session

# Import database models and functions
from database import TaskDB, get_db, init_db, engine, SessionLocal

# Initialize database tables
init_db()

app = FastAPI(title="Task Priority API",
              description="API for intelligent task prioritization",
              version="1.1.0")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class PriorityWeights(BaseModel):
    urgency: float = 0.4
    importance: float = 0.3
    effort: float = 0.2
    dependencies: float = 0.1

class TaskBase(BaseModel):
    title: str
    due_date: date
    estimated_hours: float = Field(..., gt=0, description="Estimated hours to complete the task")
    importance: int = Field(..., ge=1, le=10, description="Importance on a scale of 1-10")
    dependencies: List[str] = Field(default_factory=list, description="List of task IDs this task depends on")
    
    class Config:
        orm_mode = True
        json_encoders = {
            date: lambda v: v.isoformat()
        }

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    score: Optional[float] = None
    explanation: Optional[str] = None

class AnalysisRequest(BaseModel):
    tasks: List[TaskCreate]
    weights: Optional[PriorityWeights] = None

class AnalysisResponse(BaseModel):
    tasks: List[Task]
    strategy: str
    weights: Optional[Dict[str, float]] = None

# Priority calculation
class PriorityCalculator:
    def __init__(self, weights: Optional[PriorityWeights] = None):
        self.weights = weights or PriorityWeights()

    def calculate_score(self, task: Task, all_tasks: Dict[str, Task]) -> float:
        """Calculate priority score for a task (0-100 scale)"""
        # Normalize values
        urgency_score = self._calculate_urgency_score(task.due_date)
        importance_score = (task.importance / 10.0) * 100  # Scale 1-10 to 10-100
        effort_score = self._calculate_effort_score(task.estimated_hours)
        dependency_score = self._calculate_dependency_score(task, all_tasks)

        # Apply weights
        score = (
            self.weights.urgency * urgency_score +
            self.weights.importance * importance_score +
            self.weights.effort * effort_score +
            self.weights.dependencies * dependency_score
        )

        return min(max(score, 0), 100)  # Ensure score is between 0-100

    def _calculate_urgency_score(self, due_date: date) -> float:
        """Calculate urgency score based on due date"""
        today = date.today()
        days_until_due = (due_date - today).days
        
        if days_until_due < 0:
            # Past due - high urgency
            return 100.0
        elif days_until_due == 0:
            # Due today
            return 90.0
        elif days_until_due <= 1:
            # Due tomorrow
            return 80.0
        elif days_until_due <= 3:
            # Due in 2-3 days
            return 70.0
        elif days_until_due <= 7:
            # Due this week
            return 50.0
        elif days_until_due <= 14:
            # Due in 2 weeks
            return 30.0
        elif days_until_due <= 30:
            # Due this month
            return 20.0
        else:
            # Not urgent
            return 10.0

    def _calculate_effort_score(self, estimated_hours: float) -> float:
        """Calculate score based on effort (lower effort = higher score)"""
        if estimated_hours <= 1:
            return 100.0  # Quick win
        elif estimated_hours <= 4:
            return 80.0
        elif estimated_hours <= 8:
            return 60.0
        elif estimated_hours <= 16:
            return 40.0
        else:
            return 20.0  # Large tasks get lower score

    def _calculate_dependency_score(self, task: Task, all_tasks: Dict[str, Task]) -> float:
        """Calculate score based on how many tasks depend on this one"""
        if not task.dependencies:
            return 0.0
            
        # Check if any other tasks depend on this one
        dependent_count = sum(1 for t in all_tasks.values() if task.id in t.dependencies)
        
        if dependent_count > 0:
            return 100.0  # High score if other tasks depend on this one
        return 0.0

    def generate_explanation(self, task: Task, all_tasks: Dict[str, Task]) -> str:
        """Generate a human-readable explanation of the priority score"""
        explanations = []
        
        # Urgency explanation
        today = date.today()
        days_until_due = (task.due_date - today).days
        if days_until_due < 0:
            explanations.append(f"⚠️ Past due by {-days_until_due} days")
        elif days_until_due == 0:
            explanations.append("⏰ Due today")
        elif days_until_due <= 3:
            explanations.append(f"⏳ Due in {days_until_due} days")
            
        # Importance explanation
        if task.importance >= 8:
            explanations.append("⭐ High importance")
        elif task.importance <= 3:
            explanations.append("🔽 Low importance")
            
        # Effort explanation
        if task.estimated_hours <= 2:
            explanations.append("⚡ Quick task")
        elif task.estimated_hours >= 8:
            explanations.append("🐢 Time-consuming")
            
        # Dependencies explanation
        if task.dependencies:
            explanations.append(f"🔗 Depends on {len(task.dependencies)} tasks")
            
        # Check if other tasks depend on this one
        dependent_count = sum(1 for t in all_tasks.values() if task.id in t.dependencies)
        if dependent_count > 0:
            explanations.append(f"🔑 Blocks {dependent_count} other task{'s' if dependent_count > 1 else ''}")
            
        return ", ".join(explanations) if explanations else "No specific factors identified"

def validate_tasks(db: Session, tasks: List[Union[Task, TaskDB]], task_ids: set = None) -> None:
    """Validate tasks and their dependencies"""
    if task_ids is None:
        task_ids = {task.id for task in tasks}
    
    # Check for circular dependencies
    graph = {}
    for task in tasks:
        if hasattr(task, 'dependencies'):
            deps = [dep.id if hasattr(dep, 'id') else dep for dep in task.dependencies]
            graph[task.id] = set(deps)
    
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in task_ids:
                # Check if task exists in database
                if not db.query(TaskDB).filter(TaskDB.id == neighbor).first():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Task {node} depends on non-existent task {neighbor}"
                    )
            if neighbor not in visited:
                if has_cycle(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True
                
        rec_stack.remove(node)
        return False
    
    for task in tasks:
        visited = set()
        if task.id not in visited:
            if has_cycle(task.id, visited, set()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Circular dependency detected involving task {task.id}"
                )

# API Endpoints
# Helper function to convert DB model to Pydantic model
def task_db_to_pydantic(task_db: TaskDB) -> Task:
    task_dict = {
        'id': task_db.id,
        'title': task_db.title,
        'due_date': task_db.due_date,
        'estimated_hours': task_db.estimated_hours,
        'importance': task_db.importance,
        'score': task_db.score,
        'explanation': task_db.explanation,
        'dependencies': [dep.id for dep in task_db.dependencies]
    }
    return Task(**task_dict)

@app.post("/api/tasks/", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(task: TaskBase, db: Session = Depends(get_db)):
    """Create a new task"""
    # Create task in database
    db_task = TaskDB(
        id=str(uuid.uuid4()),
        title=task.title,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        importance=task.importance
    )
    
    # Add dependencies
    for dep_id in task.dependencies:
        dep_task = db.query(TaskDB).filter(TaskDB.id == dep_id).first()
        if dep_task:
            db_task.dependencies.append(dep_task)
    
    # Validate dependencies
    validate_tasks(db, [db_task])
    
    # Add to database
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    
    return task_db_to_pydantic(db_task)

@app.get("/api/tasks/", response_model=List[Task])
def list_tasks(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tasks"""
    tasks = db.query(TaskDB).offset(skip).limit(limit).all()
    return [task_db_to_pydantic(task) for task in tasks]

@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: str, db: Session = Depends(get_db)):
    """Get a specific task by ID"""
    task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task_db_to_pydantic(task)

@app.post("/api/tasks/analyze/", response_model=AnalysisResponse)
async def analyze_tasks(request: AnalysisRequest, db: Session = Depends(get_db)):
    """
    Analyze and prioritize a list of tasks
    """
    # Get all tasks from the database
    db_tasks = db.query(TaskDB).all()
    
    # If no tasks in request, use all tasks from database
    if not request.tasks:
        tasks = [task_db_to_pydantic(task) for task in db_tasks]
    else:
        tasks = [Task(**task.dict()) for task in request.tasks]
    
    if not tasks:
        return {"tasks": [], "strategy": "default", "weights": None}
    
    # Create a map of all tasks (from DB and request)
    all_tasks = {task.id: task for task in tasks}
    
    # Add database tasks that aren't in the request
    for db_task in db_tasks:
        if db_task.id not in all_tasks:
            all_tasks[db_task.id] = task_db_to_pydantic(db_task)
    
    # Validate tasks and dependencies
    validate_tasks(db, list(all_tasks.values()))
    
    # Initialize priority calculator with provided weights or defaults
    calculator = PriorityCalculator(weights=request.weights)
    
    # Calculate scores for all tasks
    for task in tasks:
        task.score = calculator.calculate_score(task, all_tasks)
        task.explanation = calculator.generate_explanation(task, all_tasks)
        
        # Update task in database if it exists
        db_task = db.query(TaskDB).filter(TaskDB.id == task.id).first()
        if db_task:
            db_task.score = task.score
            db_task.explanation = task.explanation
    
    db.commit()
    
    # Sort tasks by score (descending)
    sorted_tasks = sorted(tasks, key=lambda x: x.score or 0, reverse=True)
    
    return {
        "tasks": sorted_tasks,
        "strategy": "custom" if request.weights else "default",
        "weights": request.weights.dict() if request.weights else None
    }

@app.get("/api/tasks/suggest/", response_model=List[Task])
async def suggest_tasks(db: Session = Depends(get_db)):
    """
    Get top 3 suggested tasks to work on today
    """
    # Get all tasks that aren't completed
    tasks = db.query(TaskDB).all()
    
    if not tasks:
        return []
    
    # Convert to Pydantic models
    task_models = [task_db_to_pydantic(task) for task in tasks]
    
    # Create task map for dependency checking
    task_map = {task.id: task for task in task_models}
    
    # Initialize calculator with default weights
    calculator = PriorityCalculator()
    
    # Calculate scores
    for task in task_models:
        task.score = calculator.calculate_score(task, task_map)
    
    # Sort by score (descending) and take top 3
    suggested = sorted(task_models, key=lambda x: x.score or 0, reverse=True)[:3]
    
    return suggested

# Create database tables on startup
@app.on_event("startup")
def startup_event():
    init_db()

@app.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: str, db: Session = Depends(get_db)):
    """
    Mark a task as complete by deleting it
    """
    try:
        # Find the task
        task = db.query(TaskDB).filter(TaskDB.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Check if there are tasks that depend on this one
        dependent_tasks = []
        for t in db.query(TaskDB).all():
            if task_id in (t.dependencies or []):
                dependent_tasks.append(t)
        
        if dependent_tasks:
            dependent_titles = [t.title for t in dependent_tasks[:3]]  # Show first 3 for brevity
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "message": "Cannot complete task with dependent tasks",
                    "dependent_tasks": dependent_titles,
                    "total_dependents": len(dependent_tasks)
                }
            )
        
        # Delete the task
        db.delete(task)
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
