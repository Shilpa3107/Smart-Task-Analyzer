# Smart Task Analyzer

A sophisticated task management system that helps you prioritize and manage your tasks using an intelligent priority scoring algorithm.

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)
- SQLite (comes with Python)

### Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Smart-Task-Analyzer
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Initialize the database:
   ```bash
   python init_db.py
   ```

### Running the Application
1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Open your browser and navigate to:
   ```
   http://127.0.0.1:8000
   ```

## Algorithm Explanation

The priority scoring system uses a weighted algorithm that considers multiple factors to determine task priority:

1. **Urgency (40% weight)**: Tasks closer to their deadline receive higher priority. The system calculates the time remaining until the deadline and applies an exponential decay function to increase priority as the deadline approaches.

2. **Importance (30% weight)**: User-assigned importance level (1-10) that allows manual override of the automatic priority when needed.

3. **Effort (20% weight)**: Shorter tasks receive a slight priority boost to encourage quick wins and maintain momentum (following the "two-minute rule" from GTD methodology).

4. **Dependencies (10% weight)**: Tasks that block other tasks receive higher priority. The system analyzes the dependency graph and assigns higher scores to tasks that are prerequisites for multiple other tasks.

The final priority score is calculated using the formula:
```
score = (urgency * 0.4) + (importance * 0.3) + (effort * 0.2) + (dependencies * 0.1)
```

## Design Decisions

### Backend Architecture
- **FastAPI**: Chosen for its performance, automatic API documentation, and modern Python type hints.
- **SQLAlchemy ORM**: Provides a flexible and database-agnostic way to interact with the database.
- **Alembic**: Used for database migrations to handle schema changes smoothly.

### Frontend Architecture
- **Vanilla JavaScript**: Kept the frontend lightweight without additional frameworks for better performance.
- **Responsive Design**: Implemented using CSS Grid and Flexbox for a mobile-friendly interface.

### Trade-offs
1. **Simplicity vs. Features**: Chose to implement core functionality well rather than many features poorly.
2. **Manual Dependency Management**: Implemented a simple dependency system that requires manual setup rather than complex automated detection.
3. **In-Memory Processing**: Some calculations are done in memory for simplicity, which could be a limitation for very large task lists.

## Time Breakdown

- **Project Setup & Architecture**: 4 hours
  - Basic FastAPI setup
  - Database schema design
  - Project structure

- **Core Functionality**: 10 hours
  - Task CRUD operations
  - Priority algorithm implementation
  - Basic API endpoints

- **Frontend Development**: 8 hours
  - UI/UX design
  - JavaScript functionality
  - Form validation

- **Testing & Debugging**: 6 hours
  - Unit tests
  - Integration tests
  - Bug fixes

- **Documentation**: 2 hours
  - README
  - Code comments
  - API documentation

## Bonus Challenges Attempted

1. **Task Dependencies**: Implemented a system to define and visualize task dependencies.
2. **Priority Algorithm**: Created a sophisticated scoring system that considers multiple factors.
3. **Responsive Design**: Ensured the application works well on both desktop and mobile devices.

## Future Improvements

1. **User Authentication**: Add user accounts and authentication.
2. **Task Categories/Tags**: Implement a tagging system for better organization.
3. **Recurring Tasks**: Support for tasks that repeat at regular intervals.
4. **Data Export/Import**: Allow users to export/import tasks in various formats (CSV, JSON).
5. **Calendar Integration**: Sync with Google Calendar or other calendar services.
6. **Mobile App**: Develop native mobile applications for iOS and Android.
7. **Advanced Analytics**: Provide insights into task completion patterns and productivity trends.
8. **Natural Language Processing**: Allow task creation using natural language input.
9. **Collaboration Features**: Share tasks and projects with team members.
10. **Offline Support**: Enable basic functionality without an internet connection.

## Running Tests

To run the test suite:

```bash
pytest
```

For test coverage report:
```bash
pytest --cov=.
```

## API Documentation

Once the server is running, you can access:
- Interactive API docs: `http://localhost:8000/docs`
- Alternative API docs: `http://localhost:8000/redoc`

## License

MIT
