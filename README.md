# Mini RDBMS - A Custom Relational Database Management System
A lightweight, educational relational database management system (RDBMS) implemented in Python with SQL-like syntax. Features an interactive REPL interface and a modern web application built with FastAPI and React.

## 🎯 Project Overview

This project demonstrates the core concepts of relational database systems by implementing a functional RDBMS from scratch. It supports essential SQL operations, constraint enforcement, indexing, and persistence, all wrapped in an easy-to-use interface.

## ✨ Features

### Core Database Features

- **📊 Table Management**
  - Create tables with multiple column types
  - Support for INT, VARCHAR, TEXT, FLOAT, DECIMAL, and BOOL data types
  - Primary key and unique constraints

- **🔄 CRUD Operations**
  - `CREATE TABLE` - Define new table schemas
  - `INSERT INTO` - Add records to tables
  - `SELECT` - Query data with powerful filtering
  - `UPDATE` - Modify existing records
  - `DELETE FROM` - Remove records

- **⚡ Advanced Query Features**
  - **Indexing**: Automatic index creation for primary keys and unique columns
  - **Query Optimization**: Index-based lookups for improved performance
  - **JOIN Operations**: INNER JOIN support with ON conditions
  - **WHERE Clauses**: Full comparison operator support (`=`, `!=`, `>`, `<`, `>=`, `<=`)
  - **Column Projection**: Select specific columns or use `SELECT *`

- **💾 Persistence**
  - JSON-based storage (`memory.json`)
  - Automatic serialization and deserialization
  - Transaction-like behavior with immediate persistence

### User Interfaces

- **🖥️ Interactive REPL**: Command-line interface for direct SQL interaction
- **🌐 Web Application**: Modern task manager built with FastAPI backend and React frontend

## 📁 Project Structure

```
mini-rdbms/
│
├── engine.py              # Core database engine
│   ├── Database initialization
│   ├── CRUD operation handlers
│   ├── Index management
│   └── Constraint enforcement
│
├── parser.py              # SQL statement parser
│   ├── CREATE TABLE parser
│   ├── INSERT parser
│   ├── SELECT parser (with JOIN/WHERE)
│   ├── UPDATE parser
│   └── DELETE parser
│
├── repl.py               # Interactive REPL interface
│   └── Command-line SQL executor
│
├── app.py                # FastAPI web server
│   ├── RESTful API endpoints
│   └── CRUD route handlers
│
├── frontend/             # React web application
│   ├── Task management UI
│   └── Real-time SQL query display
│
├── memory.json           # Database storage (auto-generated)
└── README.md            # Project documentation
```

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or higher
- Node.js 14+ and npm (for web app frontend)
- pip (Python package manager)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/mini-rdbms.git
   cd mini-rdbms
   ```

2. **Install Python dependencies**
   ```bash
   pip install fastapi uvicorn
   ```

3. **Install frontend dependencies** (optional, for web app)
   ```bash
   cd frontend
   npm install
   cd ..
   ```

## 💻 Usage

### Option 1: Interactive REPL Mode

Launch the REPL for direct SQL interaction:

```bash
python3 repl.py
```

**Example Session:**

```sql
-- Create a users table
CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR UNIQUE, salary FLOAT);

-- Insert data
INSERT INTO users (id, name, salary) VALUES (1, 'Alice', 75000.50);
INSERT INTO users (id, name, salary) VALUES (2, 'Bob', 82000.00);
INSERT INTO users (id, name, salary) VALUES (3, 'Charlie', 68000.75);

-- Query all users
SELECT * FROM users;

-- Filter with WHERE clause
SELECT name, salary FROM users WHERE salary > 70000;

-- Update a record
UPDATE users SET salary = 85000 WHERE id = 2;

-- Create and join with another table
CREATE TABLE orders (order_id INT PRIMARY KEY, user_id INT, amount FLOAT);
INSERT INTO orders (order_id, user_id, amount) VALUES (1, 1, 150.25);
INSERT INTO orders (order_id, user_id, amount) VALUES (2, 3, 89.99);

-- Perform a JOIN
SELECT * FROM users JOIN orders ON users.id = orders.user_id;

-- Filter joined results
SELECT * FROM users JOIN orders ON users.id = orders.user_id WHERE amount > 100;

-- Delete a record
DELETE FROM users WHERE id = 1;

-- Exit the REPL
exit
```

### Option 2: Web Application

The web application provides a visual interface for database operations through a task management system.

**Start the FastAPI backend:**

```bash
python3 app.py
```

The server will start at `http://localhost:8000`

**Start the React frontend:**

```bash
cd frontend
npm start
```

The application will open at `http://localhost:3000`

**Web App Features:**
- ➕ Create new tasks with title, description, and priority
- 📋 View and filter tasks by status and priority
- ✏️ Update task status (mark as complete or reopen)
- 🗑️ Delete tasks
- 📊 Real-time statistics dashboard
- 🔍 Live SQL query visualization for educational purposes

## 🏗️ Architecture

### 1. Parser Module (`parser.py`)

The parser converts SQL-like strings into structured Python dictionaries that the engine can process.

**Supported Statements:**

- **`parse_create_table(input_data)`**
  - Parses CREATE TABLE statements
  - Extracts table name, columns, types, and constraints
  - Returns: `{"table_name": str, "columns": list, "types": list, "primary_key": str, "unique_columns": list}`

- **`parse_insert(input_data)`**
  - Parses INSERT INTO statements
  - Handles case-insensitive VALUES keyword
  - Returns: `{"table_name": str, "rows": [dict]}`

- **`parse_select(input_data)`**
  - Parses SELECT statements with optional JOIN and WHERE
  - Supports comparison operators in WHERE clauses
  - Returns: `{"table_name": str, "columns": list, "where": dict, "join": dict}`

- **`parse_update(input_data)`**
  - Parses UPDATE statements with SET and WHERE
  - Returns: `{"table_name": str, "update_data": dict, "where": dict}`

- **`parse_delete(input_data)`**
  - Parses DELETE FROM statements with WHERE
  - Returns: `{"table_name": str, "where": dict}`

### 2. Engine Module (`engine.py`)

The engine is the core of the RDBMS, managing data storage, constraints, and query execution.

**Key Components:**

- **Type System**: Maps SQL types to Python types
  ```python
  PYTHON_TYPES = {
      "int": int,
      "text": str,
      "varchar": str,
      "float": float,
      "decimal": float,
      "bool": bool,
      "boolean": bool
  }
  ```

- **Data Structure**: Each table stores:
  - Column definitions and types
  - Primary key and unique column specifications
  - Row data (list of dictionaries)
  - Indexes (dictionary mapping values to rows)

- **Index Management**:
  - Automatic index creation for primary keys and unique columns
  - String-based index keys for JSON compatibility
  - O(1) lookup for indexed equality queries

- **Constraint Enforcement**:
  - Primary key uniqueness validation
  - Unique column constraint checking
  - Type validation and casting

### 3. Storage Layer

**JSON Persistence (`memory.json`):**

```json
{
  "table_name": {
    "columns": ["col1", "col2", ...],
    "types": {"col1": "int", "col2": "varchar", ...},
    "primary_key": "col1",
    "unique_columns": ["col2"],
    "rows": [
      {"col1": 1, "col2": "value", ...},
      ...
    ],
    "indexes": {
      "col1": {
        "1": [/* row references */],
        ...
      }
    }
  }
}
```

**Key Design Decision:** Index keys are stored as strings because JSON serialization converts all dictionary keys to strings. The engine handles this by consistently using `str(value)` for all index operations.

## 🔧 Technical Details

### Indexing Strategy

The system automatically creates indexes for:
1. Primary key columns
2. Unique constraint columns

**Index Structure:**
```python
"indexes": {
    "column_name": {
        "value1": [row_ref1, row_ref2, ...],
        "value2": [row_ref3, ...],
        ...
    }
}
```

**Query Optimization:**
- Equality queries (`WHERE col = value`) on indexed columns use O(1) lookup
- Comparison queries (`>`, `<`, etc.) perform full table scan
- JOIN operations create Cartesian product, then filter

### Constraint Enforcement

**Primary Key:**
- Checked before insertion
- Prevents duplicate values
- Uses index for efficient validation

**Unique Constraints:**
- Enforced on all unique columns
- Index-based duplicate detection
- Maintains data integrity

**Type Validation:**
- Values cast to appropriate Python types on insert
- Type mismatches raise descriptive errors
- Consistent type handling across operations

## 📊 Supported SQL Syntax

### CREATE TABLE
```sql
CREATE TABLE table_name (
    column1 TYPE [PRIMARY KEY] [UNIQUE],
    column2 TYPE,
    ...
);
```

### INSERT
```sql
INSERT INTO table_name (col1, col2, ...) VALUES (val1, val2, ...);
```

### SELECT
```sql
-- Basic select
SELECT * FROM table_name;
SELECT col1, col2 FROM table_name;

-- With WHERE clause
SELECT * FROM table_name WHERE column = value;
SELECT * FROM table_name WHERE column > value;

-- With JOIN
SELECT * FROM table1 JOIN table2 ON table1.col = table2.col;

-- JOIN with WHERE
SELECT * FROM table1 JOIN table2 ON table1.col = table2.col WHERE condition;
```

### UPDATE
```sql
UPDATE table_name SET col1 = val1, col2 = val2 WHERE condition;
```

### DELETE
```sql
DELETE FROM table_name WHERE condition;
```

**Comparison Operators:** `=`, `!=`, `>`, `<`, `>=`, `<=`

## 🌐 API Documentation (FastAPI Backend)

### Endpoints

**Base URL:** `http://localhost:8000`

#### Create Task
```http
POST /api/tasks
Content-Type: application/json

{
    "title": "Task title",
    "description": "Task description",
    "priority": "High|Medium|Low"
}

Response:
{
    "success": true,
    "sql": "INSERT INTO tasks ...",
    "result": "1 row(s) inserted."
}
```

#### Get Tasks
```http
GET /api/tasks?status=Pending&priority=High

Response:
{
    "tasks": [...],
    "sql": "SELECT * FROM tasks WHERE ..."
}
```

#### Update Task
```http
PUT /api/tasks/{task_id}
Content-Type: application/json

{
    "status": "Completed"
}

Response:
{
    "success": true,
    "sql": "UPDATE tasks SET ...",
    "result": "1 row(s) updated."
}
```

#### Delete Task
```http
DELETE /api/tasks/{task_id}

Response:
{
    "success": true,
    "sql": "DELETE FROM tasks WHERE ...",
    "result": "1 row(s) deleted."
}
```

## 🧪 Testing Examples

### Basic CRUD Test
```python
# Create table
engine("CREATE TABLE test (id INT PRIMARY KEY, value VARCHAR);")

# Insert
engine("INSERT INTO test (id, value) VALUES (1, 'hello');")

# Read
result = engine("SELECT * FROM test;")
# Output: [{'id': 1, 'value': 'hello'}]

# Update
engine("UPDATE test SET value = 'world' WHERE id = 1;")

# Delete
engine("DELETE FROM test WHERE id = 1;")
```

### Constraint Testing
```python
# Primary key violation
engine("INSERT INTO test (id, value) VALUES (1, 'first');")
engine("INSERT INTO test (id, value) VALUES (1, 'duplicate');")
# Output: "Primary key 'id' violation"

# Unique constraint violation
engine("CREATE TABLE users (id INT PRIMARY KEY, email VARCHAR UNIQUE);")
engine("INSERT INTO users (id, email) VALUES (1, 'test@test.com');")
engine("INSERT INTO users (id, email) VALUES (2, 'test@test.com');")
# Output: "Unique constraint 'email' violation"
```

## 🎓 Educational Value

This project demonstrates:

1. **Database Internals**: How relational databases work under the hood
2. **SQL Parsing**: Converting text queries into executable operations
3. **Data Structures**: Using Python dictionaries and lists to model database concepts
4. **Indexing**: Implementing basic indexing for query optimization
5. **Constraint Enforcement**: Maintaining data integrity through validation
6. **API Design**: RESTful API principles with FastAPI
7. **Modern Web Stack**: Integration of backend (FastAPI) and frontend (React)

## ⚠️ Limitations

This is an educational project with intentional simplifications:

- **No NULL Support**: All columns must have values
- **Limited Aggregate Functions**: No SUM, COUNT, AVG, MAX, MIN
- **Single JOIN Type**: Only INNER JOIN is supported
- **No Sorting**: ORDER BY not implemented
- **No Grouping**: GROUP BY not implemented
- **No Transactions**: No BEGIN, COMMIT, ROLLBACK
- **Single Database**: No support for multiple databases
- **No Concurrent Access**: Not thread-safe
- **No Query Optimization**: Simple execution strategy only
- **Limited Error Handling**: Basic error messages

## 🚀 Future Enhancements

Potential improvements for learning or extension:

- [ ] Add aggregate functions (COUNT, SUM, AVG, MIN, MAX)
- [ ] Implement ORDER BY and LIMIT clauses
- [ ] Support for NULL values and IS NULL/IS NOT NULL
- [ ] LEFT JOIN, RIGHT JOIN, FULL OUTER JOIN
- [ ] GROUP BY and HAVING clauses
- [ ] Transaction support with rollback capability
- [ ] B-tree indexing for range queries
- [ ] Query execution planner
- [ ] Multi-threading and connection pooling
- [ ] Authentication and user permissions
- [ ] Backup and restore functionality
- [ ] SQL injection prevention
- [ ] Performance benchmarking tools

## 🤝 Contributing

Contributions are welcome! This is an educational project, so feel free to:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by classic RDBMS design principles
- Built as a learning exercise in database systems
- Thanks to the Python, FastAPI, and React communities

## 📧 Contact

Project Link: [https://github.com/yourusername/mini-rdbms](https://github.com/yourusername/mini-rdbms)

---

**Note:** This is an educational implementation meant for learning purposes. For production use cases, please use established database systems like PostgreSQL, MySQL, or SQLite.