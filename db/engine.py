"""
Engine module:
- Receives raw SQL-like input
- Uses parsers
- Enforces constraints
- Updates the database and saves it in the memory file
"""

from parser import parse_create_table, parse_insert, parse_select, parse_update
from pathlib import Path
import json

file_path = Path('memory.json')


PYTHON_TYPES = {
    "int": int,
    "text": str,
    "varchar": str,
    "float": float,
    "decimal": float,
    "bool": bool,
    "boolean": bool
}


def load_db():
    if not file_path.exists():
        return {}
    with file_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_db(database):
    with file_path.open("w", encoding="utf-8") as f:
        json.dump(database, f, indent=2)


def engine(input_data: str):
    database = load_db()
    input_data = input_data.strip()
    
    """
    Creates a table
    """
    result = parse_create_table(input_data)
    if result:
        table_name = result["table_name"]

        if table_name in database:
            return f"Error: Table '{table_name}' already exists."

        # Builds columns with their types
        type_dict = {}
        for col_name, col_type in zip(result["columns"], result["types"]):
            col_type = col_type.lower()
            if col_type not in PYTHON_TYPES:
                return f"Unsupported column type '{col_type}'"
            type_dict[col_name] = col_type

        database[table_name] = {
            "columns": result["columns"],
            "types": type_dict,
            "primary_key": result["primary_key"],
            "unique_columns": result["unique_columns"],
            "rows": []
        }
        save_db(database)
        return f"Table '{table_name}' created."

    """
    Inserts data into the table
    """
    result = parse_insert(input_data)
    if result:
        table_name = result["table_name"]

        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]

        for row in result["rows"]:
            # Validates and casts types
            for col, val in row.items():
                if col not in table["columns"]:
                    return f"Invalid column '{col}'"

                col_type = table["types"][col]
                python_type = PYTHON_TYPES[col_type]
                try:
                    row[col] = python_type(val)
                except ValueError:
                    return f"Invalid data type for column '{col}'"

            # Enforces primary key
            pk = table["primary_key"]
            if pk:
                for existing_row in table["rows"]:
                    if existing_row[pk] == row[pk]:
                        return f"Primary key '{pk}' violation"

            # Enforces unique constraints
            for u_col in table["unique_columns"]:
                for existing_row in table["rows"]:
                    if existing_row[u_col] == row[u_col]:
                        return f"Unique constraint '{u_col}' violation"

            table["rows"].append(row)
        
        save_db(database)
        return f"{len(result['rows'])} row(s) inserted."
    
    """
    Handles Select
    """
    result = parse_select(input_data)
    if result:
        table_name = result["table_name"]

        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]
        rows = table["rows"]
        
        # handle where clause
        where = result["where"]
        if where:
            col = where["col"]
            val = where["val"]
            
            if col not in table["columns"]:
                return f"Invalid column '{col}' in WHERE clause"
            
            col_type = table["types"][col]
            python_type = PYTHON_TYPES[col_type]

            try:
                val = python_type(val)
            except ValueError:
                return f"Invalid WHERE value type for column '{col}'"

            rows = [r for r in rows if r[col] == val]
        
        # handles select *
        if result["columns"] == ["*"]:
            return rows
        
        # validates columns
        for col in result["columns"]:
            if col not in table["columns"]:
                return f"Invalid column '{col}'"
        
        projected = []
        for row in rows:
            projected.append({col: row[col] for col in result["columns"]})
            
        return projected
    
    """
    Handles UPDATE
    """
    result = parse_update(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."
        
        table = database[table_name]
        updated = 0
        
        where = result["where"]
        col = where["column"]
        val = where["value"]
        
        # ensure where clause column exists
        if col not in table["columns"]:
            return f"Invalid column '{col}' in WHERE clause"
        
        # ensure where clause value type is correct
        col_type = table["types"][col]
        python_type = PYTHON_TYPES[col_type]
        
        try:
            val = python_type(val)
        except ValueError:
            return f"Invalid WHERE value type for column '{col}'"
        
        # start updating rows
        for row in table["rows"]:
            if row[col] == val:
                for u_col, u_val in result["update_data"].items():
                    # ensures the column to update exists
                    if u_col not in table["columns"]:
                        return f"Invalid column '{u_col}'"
                    
                    u_type = PYTHON_TYPES[table["types"][u_col]]
                    
                    try:
                        row[u_col] = u_type(u_val)
                    except ValueError:
                        return f"Invalid value for column '{u_col}'"
                
                updated += 1
        save_db(database)
        return f"{updated} row(s) updated."
                    
    
    """
    Fallback
    """
    return "Syntax error or unsupported command."
