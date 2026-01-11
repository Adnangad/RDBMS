"""
This module contains functions that parses the user input and handles the various sql statements
"""

def parse_create_table(input_data):
    """Handles CREATE statements"""
    input_data = input_data.strip()
    if not input_data.lower().startswith("create table"):
        return None
    
    #get table name
    start = len("create table ")
    open_paren = input_data.index("(")
    table_name = input_data[start:open_paren].strip()
    
    #get column definitions
    cols_str = input_data[open_paren+1 : input_data.index(")")].strip()
    columns_definitions = [c.strip() for c in cols_str.split(",")]
    
    columns = []
    types = []
    primary_key = None
    unique_columns = []
    
    for col_def in columns_definitions:
        parts = col_def.split()
        col_name = parts[0]
        col_type = parts[1]
        columns.append(col_name)
        types.append(col_type)
        
        if "primary" in col_def.lower():
            primary_key = col_name
        if "unique" in col_def.lower():
            unique_columns.append(col_name)
    
    return {
        "table_name": table_name,
        "columns": columns,
        "types": types,
        "primary_key": primary_key,
        "unique_columns": unique_columns
    }

def parse_insert(input_data):
    """Handles INSERT statements"""
    input_data = input_data.strip()

    if not input_data.lower().startswith("insert into"):
        return None

    try:
        before_values, values_part = input_data.split("values", 1)
    except ValueError:
        return None

    # get table name and columns
    open_paren = before_values.index("(")
    close_paren = before_values.index(")")
    table_name = before_values[len("insert into "):open_paren].strip()
    columns_str = before_values[open_paren+1:close_paren].strip()
    columns = [c.strip() for c in columns_str.split(",")]

    # get values
    open_paren_val = values_part.index("(")
    close_paren_val = values_part.index(")")
    values_str = values_part[open_paren_val+1:close_paren_val].strip()
    values = [v.strip().strip("'").strip('"') for v in values_str.split(",")]

    if len(columns) != len(values):
        return None

    # build row dict
    row = {columns[i]: values[i] for i in range(len(columns))}

    return {
        "table_name": table_name,
        "rows": [row]
    }

def parse_select(input_data):
    """Handles SELECT statements"""
    input_data = input_data.strip()

    if not input_data.lower().startswith("select"):
        return None
    
    if input_data.endswith(";"):
        input_data = input_data[:-1]
    
    lower = input_data.lower()
    
    if "from" not in lower:
        return None
    
    select_part, remainder = lower.split("from", 1)
    select_part = select_part.strip()
    remainder = remainder.strip()
    
    whereClause = None
    joinClause = None
    
    # handles where
    if "where" in remainder.lower():
        from_part, where_part = remainder.split("where", 1)
        table_name = from_part.strip().split()[0]
        
        where_part = where_part.strip()
        
        if "=" not in where_part:
            return None
        
        col, val = where_part.split("=", 1)
        whereClause = {
            "col": col.strip(),
            "val": val.strip()
        }
    
    # handles JOIN
    if "join" in remainder.lower():
        from_part, join_part = remainder.split("join", 1)
        table_name = from_part.strip().split()[0]
        
        join_table, on_part = join_part.split("on", 1)
        join_table = join_table.strip()
        
        left, right = on_part.split("=", 1)
        joinClause = {
            "table": join_table,
            "left": left.strip(),
            "right": right.strip()
        }
        
    else:
        table_name = remainder.split()[0]
        
    # handles select *
    if select_part.lower() == "select *":
        columns = ["*"]
    
    # handles select col
    else:
        cols_str = select_part[len("select "):]
        columns = [c.strip() for c in cols_str.split(",")]

    return {
        "table_name": table_name,
        "columns": columns,
        "where": whereClause,
        "join": joinClause
    }

def parse_update(input_data):
    """Handles UPDATE statements"""
    input_data = input_data.strip()

    lower = input_data.lower()

    if not lower.startswith("update") or "set" not in lower or "where" not in lower:
        return None

    if input_data.endswith(";"):
        input_data = input_data[:-1]
        lower = lower[:-1]

    # get table name
    update_len = len("update ")
    set_idx = lower.index("set")
    table_name = input_data[update_len:set_idx].strip()

    # get the where and set parts
    set_part = input_data[set_idx + len("set"):].strip()
    where_idx = set_part.lower().index("where")

    set_str = set_part[:where_idx].strip()
    where_str = set_part[where_idx + len("where"):].strip()

    # set column=value pairs
    update_data = {}
    for assignment in set_str.split(","):
        if "=" not in assignment:
            return None
        col, val = assignment.split("=", 1)
        update_data[col.strip()] = val.strip()

    if "=" not in where_str:
        return None

    where_col, where_val = where_str.split("=", 1)

    where_clause = {
        "column": where_col.strip(),
        "value": where_val.strip()
    }

    return {
        "table_name": table_name,
        "update_data": update_data,
        "where": where_clause
    }

def parse_delete(input_data):
    """Handles DELETE FROM"""
    input_data = input_data.strip()
    
    if not input_data.lower().startswith("delete from") or "where" not in input_data.lower():
        return None
    
    lower = input_data.lower()
    
    if input_data.endswith(";"):
        input_data = input_data[:-1]
        lower = lower[:-1]
    
    # get table name
    delete_len = len("delete from ")
    where_idx = lower.index("where")
    table_name = input_data[delete_len: where_idx].strip()
    
    # handle the where clause
    where_str = lower[where_idx + len("where"):].strip()
    
    if "=" not in where_str:
        return None
    
    where_col, where_val = where_str.split("=", 1)

    where_clause = {
        "column": where_col.strip(),
        "value": where_val.strip()
    }
    
    return {
        "table_name": table_name,
        "where": where_clause
    }