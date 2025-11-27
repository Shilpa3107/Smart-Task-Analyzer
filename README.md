# Smart Task Analyzer

An intelligent task prioritization system that helps you focus on what matters most. This application analyzes your tasks based on multiple factors and suggests the optimal order to tackle them.

## Features

- **Smart Prioritization**: Automatically sorts tasks based on urgency, importance, effort, and dependencies
- **Multiple Strategies**: Choose from different prioritization approaches
- **Interactive UI**: Clean, responsive interface for managing tasks
- **Bulk Import/Export**: Easily import/export tasks in JSON format

## 🚀 Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/Shilpa3107/Smart-Task-Analyzer.git
   cd Smart-Task-Analyzer
   ``` 
2. **Create and activate virtual environment**
   
  ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
  ```
3. **Install dependencies**

```bash
pip install -r requirements.txt
```
4. **Run the application**

```bash
# Start the backend server
uvicorn main:app --reload
```

## Open frontend in browser

open index.html  # Or manually open index.html in your browser

## 🧠 Algorithm Explanation

The prioritization algorithm considers four key factors:

- Urgency (40% weight): Based on due date proximity
- Past due: 100%
- Due today: 90%
- Next 3 days: 70-80%
- Next week: 50%
- Next month: 20-30%
- Importance (30% weight): User-defined importance (1-10 scale)
- Scaled linearly from 10-100%
- Effort (20% weight): Estimated hours to complete
- <1 hour: 100%
- 1-4 hours: 80%
- 4-8 hours: 60%
- 8-16 hours: 40%
- 16 hours: 20%
- Dependencies (10% weight): Blocking other tasks
- Tasks blocking others: +100%
- Tasks with no dependencies: 0%
  
The final score is calculated as:

  score = (urgency * 0.4) + (importance * 0.3) + (effort * 0.2) + (dependencies * 0.1)

## 🏗️ Design Decisions

- FastAPI Backend: Chosen for its performance, async support, and automatic API documentation
- SQLAlchemy ORM: For flexible database operations and future database migrations
- Vanilla JavaScript Frontend: Kept lightweight without additional frameworks
- RESTful API: Clear separation between frontend and backend

## 🏆 Bonus Challenges

-  Implemented multiple sorting strategies
-  Added task dependency validation
-  Created a responsive design
-  Added user authentication
-  Implemented task categories/tags

 ## 🚀 Future Improvements
 
  - User Accounts: Multi-user support with authentication
  - Task Categories: Organize tasks by project or category
  - Recurring Tasks: Support for repeating tasks
  - Mobile App: Native mobile application
  - Analytics: Track task completion and productivity metrics
    
### Running Tests

``` bash
pytest test_api.py -v

```

## API Documentation

Once the server is running, visit:
```bash 
API Docs: http://127.0.0.1:8000/docs
Alternative Docs: http://127.0.0.1:8000/redoc
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.
