"""
This module contains functions that parses the user input and handles the various sql statements
"""

def parse_create_table(input_data):
    """Handles CREATE statements"""
    input_data = input_data.strip()
    if not input_data.lower().startswith("create table"):
        return None
    
    # get table name
    start = len("create table ")
    open_paren = input_data.index("(")
    table_name = input_data[start:open_paren].strip()
    
    # get column definitions
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
        # make the split case-insensitive
        lower = input_data.lower()
        values_idx = lower.index("values")
        before_values = input_data[:values_idx]
        values_part = input_data[values_idx + len("values"):]
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

def parse_where_clause(where_part):
    """Parse WHERE clause with AND support"""
    conditions = []
    
    # split by 'and' (case insensitive)
    and_parts = []
    current = ""
    where_lower = where_part.lower()
    i = 0
    
    while i < len(where_part):
        if i <= len(where_part) - 4 and where_lower[i:i+4] == " and":
            # Check if next char is space or end
            if i + 4 >= len(where_part) or where_part[i+4] == " ":
                and_parts.append(current.strip())
                current = ""
                i += 4
                continue
        current += where_part[i]
        i += 1
    
    if current.strip():
        and_parts.append(current.strip())
    
    # parse each condition
    for part in and_parts:
        operator = None
        for op in ['>=', '<=', '!=', '=', '>', '<']:
            if op in part:
                operator = op
                col, val = part.split(op, 1)
                conditions.append({
                    "col": col.strip(),
                    "op": operator,
                    "val": val.strip().strip("'").strip('"')
                })
                break
    
    return conditions if conditions else None

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
    
    # find from position in lowercase, but split original input
    from_idx = lower.index("from")
    select_part = input_data[:from_idx].strip()
    remainder = input_data[from_idx + len("from"):].strip()
    remainder_lower = remainder.lower()
    
    whereClause = None
    joinClause = None
    table_name = None
    
    # parse the remainder to find join, where, etc
    if "join" in remainder_lower:
        join_idx = remainder_lower.index("join")
        
        # get the main table name (before join)
        from_part = remainder[:join_idx].strip()
        table_name = from_part.split()[0]
        
        # get everything after join
        after_join = remainder[join_idx + len("join"):].strip()
        after_join_lower = after_join.lower()
        
        # find on clause
        if "on" not in after_join_lower:
            return None
        
        on_idx = after_join_lower.index("on")
        join_table = after_join[:on_idx].strip()
        
        # get everything after on
        after_on = after_join[on_idx + len("on"):].strip()
        after_on_lower = after_on.lower()
        
        # check if there's a where clause after the join
        if "where" in after_on_lower:
            where_idx = after_on_lower.index("where")
            on_part = after_on[:where_idx].strip()
            where_part = after_on[where_idx + len("where"):].strip()
            
            # parse where with and support
            whereClause = parse_where_clause(where_part)
        else:
            on_part = after_on.strip()
        
        # parse on condition
        if "=" not in on_part:
            return None
        
        left, right = on_part.split("=", 1)
        joinClause = {
            "table": join_table,
            "left": left.strip(),
            "right": right.strip()
        }
    
    # no join, check for where
    elif "where" in remainder_lower:
        where_idx = remainder_lower.index("where")
        from_part = remainder[:where_idx].strip()
        table_name = from_part.split()[0]
        
        where_part = remainder[where_idx + len("where"):].strip()
        
        # parse where with and support
        whereClause = parse_where_clause(where_part)
    
    # no join or where, just get table name
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
        update_data[col.strip()] = val.strip().strip("'").strip('"')

    # parse where with and support
    where_clause = parse_where_clause(where_str)
    
    if not where_clause:
        return None

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
    where_str = input_data[where_idx + len("where"):].strip()
    
    # parse where with and support
    where_clause = parse_where_clause(where_str)
    
    if not where_clause:
        return None
    
    return {
        "table_name": table_name,
        "where": where_clause
    }

def parse_drop_table(input_data):
    """Handles DROP TABLE statement"""
    input_data = input_data.strip()
    
    if not input_data.lower().startswith("drop table "):
        return None
    
    if input_data.endswith(";"):
        input_data = input_data[:-1]
    
    table_name = input_data[len("drop table "):]
    if len(table_name) < 1:
        return None
    return {
        "table_name": table_name
    }
    
def alter_table(input_data):
    """Handles ALTER TABLE statement"""
    input_data = input_data.strip()
    lower = input_data.lower()
    
    if not lower.startswith("alter table"):
        return None
    if "add" not in lower and "drop column" not in lower:
        return None
    
    if input_data.endswith(";"):
        input_data = input_data[:-1]
        lower = lower[:-1]
    
    alter_type = None
    if "add" in input_data.lower():
        add_drop_idx = lower.index("add")
        alter_type = "add"
        keyword_len = len("add")
    else:
        add_drop_idx = lower.index("drop column")
        alter_type = "drop"
        keyword_len = len("drop column")
    table_name = input_data[len("alter table "): add_drop_idx].strip()
    
    # handles drop column
    if alter_type == "drop":
        column_name = input_data[lower.index("drop column") + keyword_len:]
        return {
            "alter_type": alter_type,
            "table_name": table_name.strip(),
            "column": column_name.strip()
        }
    
    # handles add column
    elif alter_type == "add":
        column_str = input_data[add_drop_idx + keyword_len:].strip()
        parts = column_str.split()
        if len(parts) >= 2:
            column = parts[0]
            data_type = parts[1]
        return {
            "alter_type": alter_type,
            "table_name": table_name.strip(),
            "column": column.strip(),
            "data_type": data_type.strip().lower()
        }