"""
FastAPI web application demonstrating CRUD operations with the custom RDBMS and user authentication
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import Optional, Annotated
from engine import engine
import uuid
import hashlib
import secrets

app = FastAPI(title="Mini RDBMS Task Manager", version="1.0.0")

allow_origins = ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

active_tokens = {}

class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserUpdate(BaseModel):
    username: str


class UserCreateResponse(BaseModel):
    message: str
    token: Optional[str] = None
    user_id: Optional[int] = None


class UserLoginResponse(BaseModel):
    message: str
    token: Optional[str] = None
    user_id: Optional[int] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = ""
    priority: Optional[str] = "Medium"
    status: Optional[str] = "Pending"


class TaskUpdate(BaseModel):
    task_id: int
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class TaskDelete(BaseModel):
    task_id: int
    user_id: Optional[int] = None


class TaskResponse(BaseModel):
    success: Optional[bool] = None
    message: Optional[str] = None
    error: Optional[str] = None
    sql: Optional[str] = None
    result: Optional[str] = None


class TasksResponse(BaseModel):
    tasks: list
    sql: Optional[str] = None


class UserResponse(BaseModel):
    user: dict


# Security utilities
def hash_password(password: str) -> str:
    """Hash a password using SHA-256 with a salt"""
    salt = "mini_rdbms_salt_2024"
    return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()


def generate_token() -> str:
    """Generate a secure random token"""
    return secrets.token_urlsafe(32)


def verify_token(x_token: str = Header(None)) -> int:
    """Verify authentication token and return user_id"""
    if not x_token:
        raise HTTPException(status_code=401, detail="Missing authentication token")
    
    user_id = active_tokens.get(x_token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user_id


def init_db():
    """Initialize the database with users and tasks tables"""
    try:
        users_result = engine(
            "CREATE TABLE users (id INT PRIMARY KEY, username VARCHAR UNIQUE, "
            "email VARCHAR UNIQUE, password TEXT);"
        )
        print(f"Users table initialization: {users_result}")
    except Exception as e:
        print(f"Users table: {e}")
    
    try:
        tasks_result = engine(
            "CREATE TABLE tasks (id INT PRIMARY KEY, title VARCHAR, "
            "description TEXT, priority VARCHAR, status VARCHAR, user_id INT);"
        )
        print(f"Tasks table initialization: {tasks_result}")
    except Exception as e:
        print(f"Tasks table: {e}")


"""USER ROUTES"""


@app.post("/api/users/register", response_model=UserCreateResponse)
async def create_user(user: UserCreate):
    """Register a new user"""
    username = user.username.replace("'", "''").strip()
    email = user.email.replace("'", "''").strip()
    
    if not username or not email:
        raise HTTPException(status_code=400, detail="Username and email cannot be empty")
    
    check_sql = f"SELECT * FROM users WHERE username = '{username}';"
    existing_user = engine(check_sql)
    
    if isinstance(existing_user, list) and len(existing_user) > 0:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    check_email_sql = f"SELECT * FROM users WHERE email = '{email}';"
    existing_email = engine(check_email_sql)
    
    if isinstance(existing_email, list) and len(existing_email) > 0:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    hashed_password = hash_password(user.password)
    
    result = engine("SELECT * FROM users;")
    next_id = len(result) + 1 if isinstance(result, list) else 1
    
    sql = (
        f"INSERT INTO users (id, username, email, password) "
        f"VALUES ({next_id}, '{username}', '{email}', '{hashed_password}');"
    )
    result = engine(sql)
    
    token = generate_token()
    active_tokens[token] = next_id
    
    return {
        'message': "User created successfully",
        'token': token,
        'user_id': next_id
    }


@app.post("/api/users/login", response_model=UserLoginResponse)
async def login_user(user: UserLogin):
    """Authenticate a user"""
    username = user.username.replace("'", "''").strip()
    
    sql = f"SELECT * FROM users WHERE username = '{username}';"
    result = engine(sql)
    
    if not isinstance(result, list) or len(result) == 0:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    user_data = result[0]
    
    hashed_input_password = hash_password(user.password)
    if user_data['password'] != hashed_input_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = generate_token()
    active_tokens[token] = user_data['id']
    
    return {
        'message': "Login successful",
        'token': token,
        'user_id': user_data['id']
    }


@app.post("/api/users/logout")
async def logout_user(user_id: int = Depends(verify_token)):
    """Logout a user (invalidate token)"""
    token_to_remove = None
    for token, uid in active_tokens.items():
        if uid == user_id:
            token_to_remove = token
            break
    
    if token_to_remove:
        del active_tokens[token_to_remove]
    
    return {'message': "Logout successful"}


@app.get("/api/users/me", response_model=UserResponse)
async def get_current_user(user_id: int = Depends(verify_token)):
    """Get current user information"""
    sql = f"SELECT id, username, email FROM users WHERE id = {user_id};"
    result = engine(sql)
    
    if not isinstance(result, list) or len(result) == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"user": result[0]}


@app.put("/", response_model=TaskResponse)
async def update_user(user_update: UserUpdate, user_id: int = Depends(verify_token)):
    """Update user information"""
    username = user_update.username.replace("'", "''").strip()
    
    if not username:
        return {"error": "Username cannot be empty"}
    
    check_sql = f"SELECT * FROM users WHERE username = '{username}' AND id != {user_id};"
    existing = engine(check_sql)
    
    if isinstance(existing, list) and len(existing) > 0:
        return {"error": "Username already taken"}
    
    sql = f"UPDATE users SET username = '{username}' WHERE id = {user_id};"
    result = engine(sql)
    
    return {"message": "Username updated successfully"}



""" Task Routes """

@app.post("/api/tasks", response_model=TaskResponse)
async def create_task(task: TaskCreate, user_id: int = Depends(verify_token)):
    """Create a new task for the authenticated user"""
    title = task.title.replace("'", "''").strip()
    description = task.description.replace("'", "''") if task.description else ""
    priority = task.priority if task.priority in ["Low", "Medium", "High"] else "Medium"
    status = task.status if task.status in ["Pending", "Completed"] else "Pending"
    
    if not title:
        return {"error": "Title cannot be empty"}
    
    result = engine("SELECT * FROM tasks;")
    next_id = len(result) + 1 if isinstance(result, list) else 1
    
    sql = (
        f"INSERT INTO tasks (id, title, description, priority, status, user_id) "
        f"VALUES ({next_id}, '{title}', '{description}', '{priority}', '{status}', {user_id});"
    )
    result = engine(sql)
    
    return {
        'message': "Task created successfully",
        'sql': sql,
        'result': str(result)
    }


@app.get('/api/tasks', response_model=TasksResponse)
async def get_tasks(
    user_id: int = Depends(verify_token),
    status: Optional[str] = None,
    priority: Optional[str] = None
):
    """Retrieve all tasks for the authenticated user with optional filters"""
    sql = f"SELECT * FROM tasks WHERE user_id = {user_id}"
    conditions = []
    
    if status and status in ["Pending", "Completed"]:
        conditions.append(f"status = '{status}'")
    if priority and priority in ["Low", "Medium", "High"]:
        conditions.append(f"priority = '{priority}'")
    
    if conditions:
        sql += " AND " + " AND ".join(conditions)
    sql += ";"
    
    result = engine(sql)
    tasks = result if isinstance(result, list) else []
    
    return {
        'tasks': tasks,
        'sql': sql
    }


@app.put('/api/tasks', response_model=TaskResponse)
async def update_task(task_update: TaskUpdate, user_id: int = Depends(verify_token)):
    """Update a task's properties (title, description, priority, status)"""
    try:
        task_id = task_update.task_id
        print("----TASK------:: ", task_update)
        print("=====TASK_ID=====:: ", type(task_id))
        
        check_sql = f"SELECT * FROM tasks WHERE id = {task_id};"
        print(check_sql)
        check_result = engine(check_sql)
        
        if not isinstance(check_result, list) or len(check_result) == 0:
            return {"error": "Task not found or unauthorized"}
        
        updates = []
        
        if task_update.title is not None:
            title = task_update.title.replace("'", "''").strip()
            if title:
                updates.append(f"title = '{title}'")
        
        if task_update.description is not None:
            description = task_update.description.replace("'", "''")
            updates.append(f"description = '{description}'")
        
        if task_update.priority is not None and task_update.priority in ["Low", "Medium", "High"]:
            updates.append(f"priority = '{task_update.priority}'")
        
        if task_update.status is not None and task_update.status in ["Pending", "Completed"]:
            print("YESSS")
            updates.append(f"status = '{task_update.status}'")
        
        if not updates:
            return {"error": "No valid fields to update"}
        
        print("UPDATES: ", updates)
        
        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = {task_id};"
        print("SQL IS-----: ", sql)
        result = engine(sql)
        
        return {
            'message': "Task updated successfully",
            'sql': sql,
            'result': str(result)
        }
    except Exception as e:
        print("EXCEPTION OCCURED:: ", e)
        return {
            'error': "Unable to update task"
        }


@app.delete('/deltask', response_model=TaskResponse)
async def delete_task(task_delete: TaskDelete, user_id: int = Depends(verify_token)):
    """Delete a task (only if it belongs to the authenticated user)"""
    task_id = task_delete.task_id
    
    check_sql = f"SELECT * FROM tasks WHERE id = {task_id} AND user_id = {user_id};"
    check_result = engine(check_sql)
    
    if not isinstance(check_result, list) or len(check_result) == 0:
        return {"error": "Task not found or unauthorized"}
    
    sql = f"DELETE FROM tasks WHERE id = {task_id};"
    result = engine(sql)
    
    return {
        'message': "Task deleted successfully",
        'sql': sql,
        'result': str(result)
    }


@app.on_event("startup")
async def startup_event():
    """Initialize database on application startup"""
    print("\nStarting Mini RDBMS Task Manager API")
    init_db()
    print("Database initialization complete\n")


if __name__ == '__main__':
    import uvicorn
    
    print("API: http://localhost:8000")
    print("Docs: http://localhost:8000/docs")
    print("Alternative docs: http://localhost:8000/redoc\n")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )