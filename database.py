from sqlalchemy import create_engine, Column, Integer, String, Date, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
import os

# Create SQLite database in the instance directory
os.makedirs('instance', exist_ok=True)
SQLALCHEMY_DATABASE_URL = "sqlite:///./instance/tasks.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Association table for many-to-many relationship between tasks
task_dependencies = Table(
    'task_dependencies',
    Base.metadata,
    Column('task_id', String, ForeignKey('tasks.id')),
    Column('depends_on_id', String, ForeignKey('tasks.id'))
)

class TaskDB(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, index=True)
    title = Column(String, index=True)
    due_date = Column(Date)
    estimated_hours = Column(Integer)
    importance = Column(Integer)
    score = Column(Integer, nullable=True)
    explanation = Column(String, nullable=True)
    
    # Self-referential relationship for dependencies
    dependencies = relationship(
        'TaskDB',
        secondary=task_dependencies,
        primaryjoin=(id == task_dependencies.c.task_id),
        secondaryjoin=(id == task_dependencies.c.depends_on_id),
        backref="depends_on_me"
    )

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
