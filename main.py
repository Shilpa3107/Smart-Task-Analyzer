from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import json
from enum import Enum
import uuid
from collections import defaultdict

app = FastAPI(title="Task Priority API",
              description="API for intelligent task prioritization",
              version="1.0.0")

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

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    score: Optional[float] = None
    explanation: Optional[str] = None

    class Config:
        json_encoders = {
            date: lambda v: v.isoformat()
        }

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

def validate_tasks(tasks: List[Task]) -> None:
    """Validate tasks and their dependencies"""
    task_ids = {task.id for task in tasks}
    
    # Check for circular dependencies
    graph = {task.id: set(task.dependencies) for task in tasks}
    
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)
        
        for neighbor in graph.get(node, set()):
            if neighbor not in task_ids:
                raise HTTPException(status_code=400, detail=f"Task {node} depends on non-existent task {neighbor}")
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
                raise HTTPException(status_code=400, detail=f"Circular dependency detected involving task {task.id}")

# API Endpoints
@app.post("/api/tasks/analyze/", response_model=AnalysisResponse)
async def analyze_tasks(request: AnalysisRequest):
    """
    Analyze and prioritize a list of tasks
    """
    # Convert input tasks to our internal Task model with IDs
    tasks = [Task(**task.dict()) for task in request.tasks]
    
    # Validate tasks and dependencies
    validate_tasks(tasks)
    
    # Create a map of task IDs to tasks
    task_map = {task.id: task for task in tasks}
    
    # Initialize priority calculator with provided weights or defaults
    calculator = PriorityCalculator(weights=request.weights)
    
    # Calculate scores for all tasks
    for task in tasks:
        task.score = calculator.calculate_score(task, task_map)
        task.explanation = calculator.generate_explanation(task, task_map)
    
    # Sort tasks by score (descending)
    sorted_tasks = sorted(tasks, key=lambda x: x.score, reverse=True)
    
    return {
        "tasks": sorted_tasks,
        "strategy": "custom" if request.weights else "default",
        "weights": request.weights.dict() if request.weights else None
    }

@app.get("/api/tasks/suggest/")
async def suggest_tasks():
    """
    Get top 3 suggested tasks to work on today
    This is a simplified version that would typically use stored tasks in a real app
    """
    return {"message": "This endpoint would return top 3 tasks to work on today. "
                      "In a real implementation, this would query your task database."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
