import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useSpring, animated } from 'react-spring';
import Popup from 'reactjs-popup';
import './Home.css';

function Home() {
    const token = sessionStorage.getItem('token');
    const user_id = sessionStorage.getItem('user_id');
    const [tasks, setTasks] = useState([]);
    const [filteredTasks, setFilteredTasks] = useState([]);
    const [user, setUser] = useState({});
    
    // Task creation fields - ALL 4 FIELDS
    const [taskTitle, setTaskTitle] = useState("");
    const [taskDescription, setTaskDescription] = useState("");
    const [taskPriority, setTaskPriority] = useState("Medium");
    const [taskStatus, setTaskStatus] = useState("Pending");
    
    const [message, setMessage] = useState("");
    const [errorMessage, setError] = useState("");
    const [username, setUserName] = useState("");
    const [lastSQL, setLastSQL] = useState("");
    const [statusFilter, setStatusFilter] = useState("all");
    const [priorityFilter, setPriorityFilter] = useState("all");
    const [showSQLPreview, setShowSQLPreview] = useState(true);
    const navigate = useNavigate();

    // Statistics
    const totalTasks = tasks.length;
    const completedTasks = tasks.filter(t => t.status === "Completed").length;
    const pendingTasks = tasks.filter(t => t.status === "Pending").length;

    useEffect(() => {
        if (!token) {
            navigate('/login');
            return;
        }
        
        getTasks();
        getUser();
    }, [token, navigate]);

    // Filter tasks whenever tasks or filters change
    useEffect(() => {
        filterTasks();
    }, [tasks, statusFilter, priorityFilter]);

    const filterTasks = () => {
        let filtered = [...tasks];
        
        if (statusFilter !== "all") {
            filtered = filtered.filter(t => t.status === statusFilter);
        }
        
        if (priorityFilter !== "all") {
            filtered = filtered.filter(t => t.priority === priorityFilter);
        }
        
        setFilteredTasks(filtered);
    };

    const getTasks = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/tasks', {
                method: "GET",
                headers: {
                    'Content-Type': 'application/json',
                    'X-Token': token
                }
            });

            if (response.status === 200) {
                const data = await response.json();
                setTasks(data.tasks);
                if (data.sql) {
                    setLastSQL(data.sql);
                }
            } else if (response.status === 401) {
                alert('Session expired. Redirecting to login.');
                sessionStorage.clear();
                navigate('/login');
            } else {
                setError('Failed to fetch tasks');
            }
        } catch (error) {
            console.error('Fetch tasks error:', error);
            setError('Unable to fetch tasks at this time');
        }
    };
    
    const getUser = async () => {
        try {
            const response = await fetch('http://127.0.0.1:8000/api/users/me', {
                method: "GET",
                headers: {
                    'Content-Type': 'application/json',
                    'X-Token': token
                }
            });

            if (response.status === 200) {
                const data = await response.json();
                setUser(data.user);
                setUserName(data.user.username);
            } else if (response.status === 401) {
                alert('Session expired. Redirecting to login.');
                sessionStorage.clear();
                navigate('/login');
            } else {
                setError('Failed to fetch user details');
            }
        } catch (error) {
            console.error('Fetch user error:', error);
            setError('Unable to fetch user details at this time');
        }
    };

    const createATask = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/tasks', {
                method: "POST",
                headers: {
                    'Content-Type': 'application/json',
                    'X-Token': token
                },
                body: JSON.stringify({ 
                    title: taskTitle,
                    description: taskDescription,
                    priority: taskPriority,
                    status: taskStatus
                }),
            });

            const rez = await response.json();
            if (response.status === 200) {
                setMessage(rez.message);
                if (rez.sql) {
                    setLastSQL(rez.sql);
                }
                // Reset form
                setTaskTitle("");
                setTaskDescription("");
                setTaskPriority("Medium");
                setTaskStatus("Pending");
                // Refresh tasks without page reload
                await getTasks();
                setTimeout(() => setMessage(""), 3000);
            } else {
                setError(rez.error || 'Failed to create task');
                setTimeout(() => setError(""), 3000);
            }
        } catch (error) {
            console.error('Create task error:', error);
            setError('Unable to create task at this time');
            setTimeout(() => setError(""), 3000);
        }
    };

    const updateTaskStatus = async (taskId, currentStatus) => {
        console.log('Updating task ID:', taskId, 'Current Status:', currentStatus);
        const newStatus = currentStatus === "Pending" ? "Completed" : "Pending";
        
        try {
            const response = await fetch('http://127.0.0.1:8000/api/tasks', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Token': token
                },
                body: JSON.stringify({ 
                    task_id: taskId,
                    status: newStatus
                })
            });
            console.log('Response status:', response.status);
            console.log('RESPONSE::: ', response);

            const rez = await response.json();
            if (response.status === 200) {
                if (rez.sql) {
                    setLastSQL(rez.sql);
                }
                // Refresh tasks without page reload
                await getTasks();
                setMessage(rez.message);
                setTimeout(() => setMessage(""), 3000);
            } else {
                alert(rez.error || 'Failed to update task');
            }
        } catch (error) {
            console.error('Update task error:', error);
            alert('Unable to update task at this time');
        }
    };

    const deleteTask = async (taskId) => {
        if (!window.confirm('Are you sure you want to delete this task?')) {
            return;
        }
        
        try {
            const response = await fetch('http://127.0.0.1:8000/deltask', {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Token': token
                },
                body: JSON.stringify({ task_id: taskId, user_id: parseInt(user_id) })
            });

            const rez = await response.json();
            if (response.status === 200) {
                if (rez.sql) {
                    setLastSQL(rez.sql);
                }
                // Refresh tasks without page reload
                await getTasks();
                setMessage(rez.message);
                setTimeout(() => setMessage(""), 3000);
            } else {
                alert(rez.error || 'Failed to delete task');
            }
        } catch (error) {
            console.error('Delete task error:', error);
            alert('Unable to delete task at this time');
        }
    };
    
    const updateUser = async (e) => {
        e.preventDefault();
        setMessage("");
        setError("");
        
        try {
            const response = await fetch('http://127.0.0.1:8000/', {
                method: 'PUT',
                headers: { 
                    'Content-Type': 'application/json', 
                    'X-Token': token 
                },
                body: JSON.stringify({ username: username })
            });
            
            const data = await response.json();
            if (response.status === 200) {
                setMessage(data.message);
                await getUser();
                setTimeout(() => setMessage(""), 3000);
            } else {
                setError(data.error || 'Failed to update username');
                setTimeout(() => setError(""), 3000);
            }
        } catch (error) {
            console.error('Update user error:', error);
            setError('Unable to update account details');
            setTimeout(() => setError(""), 3000);
        }
    };

    const handleLogout = () => {
        sessionStorage.clear();
        navigate('/login');
    };

    return (
        <div className="page-container">
            <div className="main-container">
                <header className="page-header">
                    <div className="header-content">
                        <h1>Task Manager</h1>
                        <p>Manage your tasks efficiently</p>
                    </div>
                    <div className="header-actions">
                        <Popup
                            trigger={<button className="btn-account">👤 Account</button>}
                            modal
                            contentStyle={{
                                width: '500px',
                                padding: '30px',
                                backgroundColor: 'white',
                                borderRadius: '12px',
                                boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
                            }}
                            overlayStyle={{
                                backgroundColor: 'rgba(0, 0, 0, 0.7)',
                            }}
                        >
                            {close => (
                                <div className="popup-content">
                                    <h3 style={{ marginBottom: '20px', color: '#4CAF50' }}>Manage Account</h3>
                                    <form onSubmit={(e) => { updateUser(e); }}>
                                        <div className="form-group">
                                            <label>Username</label>
                                            <input
                                                type="text"
                                                required
                                                placeholder="Update username"
                                                value={username}
                                                onChange={(e) => setUserName(e.target.value)}
                                            />
                                        </div>
                                        <button type="submit" className="btn-primary">Update Username</button>
                                    </form>
                                    {message && <p className="success-message">{message}</p>}
                                    {errorMessage && <p className="error-message">{errorMessage}</p>}
                                    <div className="user-details">
                                        <p><strong>Email:</strong> {user.email}</p>
                                        <p><strong>Username:</strong> {user.username}</p>
                                    </div>
                                    <button onClick={close} className="btn-close">Close</button>
                                </div>
                            )}
                        </Popup>
                        <button onClick={handleLogout} className="btn-logout">🚪 Logout</button>
                    </div>
                </header>

                <div className="content">
                    {/* Global Messages */}
                    {message && (
                        <div className="global-message success-message">
                            {message}
                        </div>
                    )}
                    {errorMessage && (
                        <div className="global-message error-message">
                            {errorMessage}
                        </div>
                    )}

                    {/* Statistics */}
                    <div className="stats">
                        <div className="stat-card">
                            <div className="stat-value">{totalTasks}</div>
                            <div className="stat-label">Total Tasks</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{completedTasks}</div>
                            <div className="stat-label">Completed</div>
                        </div>
                        <div className="stat-card">
                            <div className="stat-value">{pendingTasks}</div>
                            <div className="stat-label">Pending</div>
                        </div>
                    </div>

                    {/* SQL Preview Toggle */}
                    <div className="sql-toggle">
                        <label>
                            <input 
                                type="checkbox" 
                                checked={showSQLPreview} 
                                onChange={(e) => setShowSQLPreview(e.target.checked)}
                            />
                            <span>Show SQL Queries</span>
                        </label>
                    </div>

                    {/* SQL Preview */}
                    {showSQLPreview && lastSQL && (
                        <div className="sql-preview">
                            <strong>Last SQL Query:</strong>
                            <code>{lastSQL}</code>
                        </div>
                    )}

                    {/* ===== CREATE TASK SECTION===== */}
                    <div className="section">
                        <h2>Create New Task</h2>
                        <form onSubmit={createATask} className="task-form">
                            {/* FIELD 1: TITLE (Required) */}
                            <div className="form-group">
                                <label>Title *</label>
                                <input
                                    type="text"
                                    required
                                    placeholder="Enter task title"
                                    value={taskTitle}
                                    onChange={(e) => setTaskTitle(e.target.value)}
                                />
                            </div>
                            
                            {/* FIELD 2: DESCRIPTION (Optional) */}
                            <div className="form-group">
                                <label>Description</label>
                                <textarea
                                    rows="3"
                                    placeholder="Enter task description (optional)"
                                    value={taskDescription}
                                    onChange={(e) => setTaskDescription(e.target.value)}
                                />
                            </div>
                            
                            {/* FIELDS 3 & 4: PRIORITY and STATUS (Side by side) */}
                            <div className="form-row">
                                {/* FIELD 3: PRIORITY */}
                                <div className="form-group">
                                    <label>Priority</label>
                                    <select
                                        value={taskPriority}
                                        onChange={(e) => setTaskPriority(e.target.value)}
                                    >
                                        <option value="Low">Low</option>
                                        <option value="Medium">Medium</option>
                                        <option value="High">High</option>
                                    </select>
                                </div>
                                
                                {/* FIELD 4: STATUS */}
                                <div className="form-group">
                                    <label>Status</label>
                                    <select
                                        value={taskStatus}
                                        onChange={(e) => setTaskStatus(e.target.value)}
                                    >
                                        <option value="Pending">Pending</option>
                                        <option value="Completed">Completed</option>
                                    </select>
                                </div>
                            </div>
                            
                            <button type="submit" className="btn-primary">Create Task</button>
                        </form>
                    </div>

                    {/* View Tasks Section */}
                    <div className="section">
                        <h2>Your Tasks</h2>
                        
                        {/* Filter Section */}
                        <div className="filter-section">
                            <div className="filter-group">
                                <label htmlFor="statusFilter">Status:</label>
                                <select 
                                    id="statusFilter" 
                                    value={statusFilter} 
                                    onChange={(e) => setStatusFilter(e.target.value)}
                                    className="filter-select"
                                >
                                    <option value="all">All Status</option>
                                    <option value="Pending">Pending</option>
                                    <option value="Completed">Completed</option>
                                </select>
                            </div>
                            
                            <div className="filter-group">
                                <label htmlFor="priorityFilter">Priority:</label>
                                <select 
                                    id="priorityFilter" 
                                    value={priorityFilter} 
                                    onChange={(e) => setPriorityFilter(e.target.value)}
                                    className="filter-select"
                                >
                                    <option value="all">All Priorities</option>
                                    <option value="Low">Low</option>
                                    <option value="Medium">Medium</option>
                                    <option value="High">High</option>
                                </select>
                            </div>
                            
                            <button onClick={getTasks} className="btn-refresh">Refresh</button>
                        </div>

                        <div className="task-list">
                            {filteredTasks.length === 0 ? (
                                <div className="empty-state">
                                    <svg fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd"/>
                                    </svg>
                                    <h3>No tasks found</h3>
                                    <p>
                                        {statusFilter === "all" && priorityFilter === "all"
                                            ? "Create a new task to get started!" 
                                            : "No tasks match the current filters."}
                                    </p>
                                </div>
                            ) : (
                                filteredTasks.map(task => (
                                    <div key={task.id} className="task-card">
                                        <div className="task-header">
                                            <div className="task-title">{task.title}</div>
                                            <span className={`task-status ${task.status === 'Completed' ? 'status-completed' : 'status-pending'}`}>
                                                {task.status}
                                            </span>
                                        </div>
                                        
                                        {task.description && (
                                            <div className="task-description">{task.description}</div>
                                        )}
                                        
                                        <div className="task-meta">
                                            <span> Priority: <strong>{task.priority}</strong></span>
                                            <span> ID: {task.id}</span>
                                        </div>
                                        
                                        <div className="task-actions">
                                            {task.status === "Pending" ? (
                                                <button onClick={() => updateTaskStatus(task.id, task.status)} className="btn-primary">
                                                    ✓ Complete
                                                </button>
                                            ) : (
                                                <button onClick={() => updateTaskStatus(task.id, task.status)} className="btn-secondary">
                                                    ↶ Reopen
                                                </button>
                                            )}
                                            <button onClick={() => deleteTask(task.id)} className="btn-danger">
                                                 Delete
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Home;