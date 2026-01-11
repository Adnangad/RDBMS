"""
Engine module:
- Receives raw SQL-like input
- Uses parsers
- Enforces constraints
- Updates the database and saves it in a JSON file
- Supports indexing for primary keys and unique columns
"""

from parser import parse_create_table, parse_insert, parse_select, parse_update, parse_delete
from pathlib import Path
import json

file_path = Path("memory.json")

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
    Handles Create
    """
    result = parse_create_table(input_data)
    if result:
        table_name = result["table_name"]
        if table_name in database:
            return f"Error: Table '{table_name}' already exists."

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
            "rows": [],
            "indexes": {}
        }

        # Initialize indexes on primary and unique columns
        for col in [result["primary_key"]] + result["unique_columns"]:
            if col:
                database[table_name]["indexes"][col] = {}

        save_db(database)
        return f"Table '{table_name}' created."

    """
    Handles Insert
    """
    result = parse_insert(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]

        for row in result["rows"]:
            # Validate and cast types
            for col, val in row.items():
                if col not in table["columns"]:
                    return f"Invalid column '{col}'"
                col_type = table["types"][col]
                python_type = PYTHON_TYPES[col_type]
                try:
                    row[col] = python_type(val)
                except ValueError:
                    return f"Invalid data type for column '{col}'"

            # Enforce primary key (use string keys for JSON compatibility)
            pk = table["primary_key"]
            if pk:
                pk_val = row[pk]
                if pk in table["indexes"] and str(pk_val) in table["indexes"][pk]:
                    return f"Primary key '{pk}' violation"

            # Enforce unique constraints (use string keys for JSON compatibility)
            for u_col in table["unique_columns"]:
                if u_col and u_col in table["indexes"]:
                    u_val = row[u_col]
                    if str(u_val) in table["indexes"][u_col]:
                        return f"Unique constraint '{u_col}' violation"

            # Append row
            table["rows"].append(row)

            # Update indexes (use string keys for JSON compatibility)
            for idx_col, idx_map in table["indexes"].items():
                idx_val = row[idx_col]
                idx_map.setdefault(str(idx_val), []).append(row)

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

        # Handle JOIN
        join = result["join"]
        if join:
            table_name2 = join["table"]
            if table_name2 not in database:
                return f"Error: Table '{table_name2}' does not exist."
            table2 = database[table_name2]

            left_table, left_col = join["left"].split(".")
            right_table, right_col = join["right"].split(".")

            if left_table != table_name:
                return "Invalid JOIN condition"

            joined_rows = []
            for r1 in table["rows"]:
                for r2 in table2["rows"]:
                    if r1[left_col] == r2[right_col]:
                        combined = {}
                        combined.update({f"{table_name}.{k}": v for k, v in r1.items()})
                        combined.update({f"{table_name2}.{k}": v for k, v in r2.items()})
                        joined_rows.append(combined)
            rows = joined_rows

        # Handle WHERE
        where = result["where"]
        if where:
            col = where["col"]
            val = where["val"]
            op = where.get("op", "=")  # Default to equality if no operator specified

            # For joined tables, column names have table prefix
            if join:
                # Check if column exists in joined rows (might be prefixed)
                if rows:
                    # Try to find the column (with or without prefix)
                    actual_col = None
                    if col in rows[0]:
                        actual_col = col
                    else:
                        # Try with table prefix
                        for potential_col in rows[0].keys():
                            if potential_col.endswith("." + col):
                                actual_col = potential_col
                                break
                    
                    if actual_col is None:
                        return f"Invalid column '{col}' in WHERE clause"
                    
                    # Type conversion for joined rows
                    try:
                        val = type(rows[0][actual_col])(val)
                    except (ValueError, KeyError):
                        return f"Invalid WHERE value type for column '{col}'"
                    
                    # Apply comparison operator
                    if op == "=":
                        rows = [r for r in rows if r.get(actual_col) == val]
                    elif op == "!=":
                        rows = [r for r in rows if r.get(actual_col) != val]
                    elif op == ">":
                        rows = [r for r in rows if r.get(actual_col) > val]
                    elif op == "<":
                        rows = [r for r in rows if r.get(actual_col) < val]
                    elif op == ">=":
                        rows = [r for r in rows if r.get(actual_col) >= val]
                    elif op == "<=":
                        rows = [r for r in rows if r.get(actual_col) <= val]
                else:
                    rows = []
            else:
                # For non-joined queries, validate column exists
                if col not in table["columns"]:
                    return f"Invalid column '{col}' in WHERE clause"
                
                # Convert value to proper type using table schema
                col_type = table["types"][col]
                python_type = PYTHON_TYPES[col_type]
                try:
                    val = python_type(val)
                except ValueError:
                    return f"Invalid WHERE value type for column '{col}'"

                # Apply comparison operator
                if op == "=" and col in table["indexes"]:
                    # Use index only for equality
                    rows = table["indexes"][col].get(str(val), [])
                else:
                    # For other operators or non-indexed columns, filter rows
                    if op == "=":
                        rows = [r for r in rows if r[col] == val]
                    elif op == "!=":
                        rows = [r for r in rows if r[col] != val]
                    elif op == ">":
                        rows = [r for r in rows if r[col] > val]
                    elif op == "<":
                        rows = [r for r in rows if r[col] < val]
                    elif op == ">=":
                        rows = [r for r in rows if r[col] >= val]
                    elif op == "<=":
                        rows = [r for r in rows if r[col] <= val]

        # Handle SELECT *
        if result["columns"] == ["*"]:
            return rows

        # Projection
        if rows:
            for col in result["columns"]:
                if col not in rows[0]:
                    return f"Invalid column '{col}'"
        return [{col: row[col] for col in result["columns"]} for row in rows]

    
    """
    Handles Update
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

        if col not in table["columns"]:
            return f"Invalid column '{col}' in WHERE clause"

        col_type = table["types"][col]
        python_type = PYTHON_TYPES[col_type]

        try:
            val = python_type(val)
        except ValueError:
            return f"Invalid WHERE value type for column '{col}'"

        for row in table["rows"]:
            if row[col] == val:
                for u_col, u_val in result["update_data"].items():
                    if u_col not in table["columns"]:
                        return f"Invalid column '{u_col}'"
                    u_type = PYTHON_TYPES[table["types"][u_col]]
                    old_val = row[u_col]
                    new_val = u_type(u_val)
                    row[u_col] = new_val

                    # Update indexes (use string keys for JSON compatibility)
                    if u_col in table["indexes"]:
                        if str(old_val) in table["indexes"][u_col]:
                            table["indexes"][u_col][str(old_val)].remove(row)
                            if not table["indexes"][u_col][str(old_val)]:
                                del table["indexes"][u_col][str(old_val)]
                        table["indexes"][u_col].setdefault(str(new_val), []).append(row)

                updated += 1

        save_db(database)
        return f"{updated} row(s) updated."

    """
    Handles Delete
    """
    result = parse_delete(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]
        where = result["where"]
        col = where["column"]
        val = where["value"]

        if col not in table["columns"]:
            return f"Invalid column '{col}' in WHERE clause"

        col_type = table["types"][col]
        python_type = PYTHON_TYPES[col_type]
        try:
            val = python_type(val)
        except ValueError:
            return f"Invalid WHERE value type for column '{col}'"

        # Delete rows and update indexes (use string keys for JSON compatibility)
        rows_to_delete = [row for row in table["rows"] if row[col] == val]

        for row in rows_to_delete:
            for idx_col, idx_map in table["indexes"].items():
                idx_val = row[idx_col]
                if str(idx_val) in idx_map:
                    idx_map[str(idx_val)].remove(row)
                    if not idx_map[str(idx_val)]:
                        del idx_map[str(idx_val)]

        table["rows"] = [row for row in table["rows"] if row[col] != val]

        deleted = len(rows_to_delete)
        save_db(database)
        return f"{deleted} row(s) deleted."
    
    """
    Handles Fallback
    """
    return "Syntax error or unsupported command."