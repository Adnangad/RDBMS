"""
Engine module:
- Receives raw SQL-like input
- Uses parsers
- Enforcess constraints
- Updates the database and saves it in a JSON file
- Supports indexing for primary keys and unique columns
"""

from parser import parse_create_table, parse_insert, parse_select, parse_update, parse_delete
from pathlib import Path
import json
import operator

# Map strings operators to python functions
ops = {
    '>=': operator.ge,
    '<=': operator.le,
    '!=': operator.ne,
    '=': operator.eq,
    '==': operator.eq,
    '>': operator.gt,
    '<': operator.lt
}

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


def rebuild_indexes(table):
    """Rebuild all indexes for a table from scratch"""
    # clear existing indexes
    for idx_col in table["indexes"]:
        table["indexes"][idx_col] = {}
    
    # rebuild from rows
    for row in table["rows"]:
        for idx_col in table["indexes"]:
            idx_val = row[idx_col]
            table["indexes"][idx_col].setdefault(str(idx_val), []).append(row)


def apply_where_conditions(rows, conditions, table=None, is_joined=False):
    """Apply WHERE conditions to rows (supports AND)"""
    if not conditions:
        return rows
    
    # ensures conditions is a list (for backward compatibility)
    if isinstance(conditions, dict):
        conditions = [conditions]
    
    filtered_rows = rows
    
    for condition in conditions:
        col = condition["col"]
        val = condition["val"]
        op = condition.get("op", "=")
        
        if is_joined:
            # for joined tables, handle prefixed columns
            if filtered_rows:
                actual_col = None
                if col in filtered_rows[0]:
                    actual_col = col
                else:
                    # try with table prefix
                    for potential_col in filtered_rows[0].keys():
                        if potential_col.endswith("." + col):
                            actual_col = potential_col
                            break
                
                if actual_col is None:
                    return []  # column not found
                
                try:
                    val = type(filtered_rows[0][actual_col])(val)
                except (ValueError, KeyError):
                    return []
                
                # applys operator
                if op == "=":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) == val]
                elif op == "!=":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) != val]
                elif op == ">":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) > val]
                elif op == "<":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) < val]
                elif op == ">=":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) >= val]
                elif op == "<=":
                    filtered_rows = [r for r in filtered_rows if r.get(actual_col) <= val]
        else:
            # for non-joined queries
            if col not in table["columns"]:
                return []
            
            col_type = table["types"][col]
            python_type = PYTHON_TYPES[col_type]
            try:
                val = python_type(val)
            except ValueError:
                return []
            
            # use index for first condition if possible (equality only)
            if filtered_rows == table["rows"] and op == "=" and col in table["indexes"]:
                filtered_rows = table["indexes"][col].get(str(val), [])
            else:
                # apply operator
                if op == "=":
                    filtered_rows = [r for r in filtered_rows if r[col] == val]
                elif op == "!=":
                    filtered_rows = [r for r in filtered_rows if r[col] != val]
                elif op == ">":
                    filtered_rows = [r for r in filtered_rows if r[col] > val]
                elif op == "<":
                    filtered_rows = [r for r in filtered_rows if r[col] < val]
                elif op == ">=":
                    filtered_rows = [r for r in filtered_rows if r[col] >= val]
                elif op == "<=":
                    filtered_rows = [r for r in filtered_rows if r[col] <= val]
    
    return filtered_rows


def engine(input_data: str):
    database = load_db()
    input_data = input_data.strip()
    
    """
    handles create
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

        # initializes indexes on primary and unique columns
        for col in [result["primary_key"]] + result["unique_columns"]:
            if col:
                database[table_name]["indexes"][col] = {}

        save_db(database)
        return f"Table '{table_name}' created."

    """
    handles insert
    """
    result = parse_insert(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]

        for row in result["rows"]:
            # validates and cast types
            for col, val in row.items():
                if col not in table["columns"]:
                    return f"Invalid column '{col}'"
                col_type = table["types"][col]
                python_type = PYTHON_TYPES[col_type]
                try:
                    row[col] = python_type(val)
                except ValueError:
                    return f"Invalid data type for column '{col}'"

            # enforces primary key (use string keys for json compatibility)
            pk = table["primary_key"]
            if pk:
                pk_val = row[pk]
                if pk in table["indexes"] and str(pk_val) in table["indexes"][pk]:
                    return f"Primary key '{pk}' violation"

            # enforces unique constraints (use string keys for json compatibility)
            for u_col in table["unique_columns"]:
                if u_col and u_col in table["indexes"]:
                    u_val = row[u_col]
                    if str(u_val) in table["indexes"][u_col]:
                        return f"Unique constraint '{u_col}' violation"

            # append row
            table["rows"].append(row)

        # rebuild indexes after insertion
        rebuild_indexes(table)
        
        save_db(database)
        return f"{len(result['rows'])} row(s) inserted."

    """
    handles select
    """
    result = parse_select(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]
        rows = table["rows"]

        # handle join
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

        # handles where with and support
        where = result["where"]
        if where:
            if join:
                rows = apply_where_conditions(rows, where, is_joined=True)
            else:
                rows = apply_where_conditions(rows, where, table=table, is_joined=False)

        # handles select *
        if result["columns"] == ["*"]:
            return rows

        if rows:
            for col in result["columns"]:
                if col not in rows[0]:
                    return f"Invalid column '{col}'"
        return [{col: row[col] for col in result["columns"]} for row in rows]

    
    """
    handles update
    """
    result = parse_update(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]
        updated = 0

        where = result["where"]
        
        # ensures where is a list
        if isinstance(where, dict):
            where = [where]
        
        # validates all WHERE conditions
        for condition in where:
            col = condition["col"]
            if col not in table["columns"]:
                return f"Invalid column '{col}' in WHERE clause"

        # checks for unique constraint violations before updating
        #rows_to_update = apply_where_conditions(table["rows"], where, table=table, is_joined=False)
        
        for u_col, u_val in result["update_data"].items():
            if u_col not in table["columns"]:
                return f"Invalid column '{u_col}'"
                
            # checks if this column has a unique constraint
            if u_col == table["primary_key"] or u_col in table["unique_columns"]:
                u_type = PYTHON_TYPES[table["types"][u_col]]
                new_val = u_type(u_val)
                    
                # checks if this new value already exists in another row
                for other_row in table["rows"]:
                    if other_row.get(u_col) == new_val:
                        if u_col == table["primary_key"]:
                            return f"Primary key '{u_col}' violation"
                        else:
                            return f"Unique constraint '{u_col}' violation"

        # performs the update
        for row in table['rows']:
            for u_col, u_val in result["update_data"].items():
                u_type = PYTHON_TYPES[table["types"][u_col]]
                row[u_col] = u_type(u_val)
            updated += 1

        # rebuilds indexes after update
        rebuild_indexes(table)

        save_db(database)
        return f"{updated} row(s) updated."

    """
    handles delete
    """
    result = parse_delete(input_data)
    if result:
        table_name = result["table_name"]
        if table_name not in database:
            return f"Error: Table '{table_name}' does not exist."

        table = database[table_name]
        where = result["where"]
        
        # ensures where is a list
        if isinstance(where, dict):
            where = [where]
        
        original_count = len(table["rows"])
        
        # Validates all WHERE conditions and applys the filters
        for condition in where:
            col = condition["col"]
            val = condition["val"]
            op_str = condition["op"]
            if col not in table["columns"]:
                return f"Invalid column '{col}' in WHERE clause"
            col_type = table["types"][col]
            python_type = PYTHON_TYPES[col_type]
            try:
                val = python_type(val)
            except ValueError:
                return f"Invalid WHERE value type for column '{col}'"
            print("Operator is: ", op_str)
            table["rows"] = [row for row in table["rows"] if not ops[op_str](row[col], val)]
            

        deleted = original_count - len(table["rows"])
        # rebuilds indexes after deletion
        rebuild_indexes(table)

        save_db(database)
        return f"{deleted} row(s) deleted."
    
    """
    handles fallback
    """
    return "Syntax error or unsupported command."