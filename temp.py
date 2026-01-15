input_data = "ALTER TABLE table_name ADD column_name datatype;"
lower = input_data.lower()
if not input_data.lower().startswith("alter table") or "add" not in lower or "drop column" not in lower:
    print("NONE")
if input_data.endswith(";"):
    input_data = input_data[:-1]
    lower = lower[:-1]

add_drop_idx = 0
alter_type = None
if "add" in input_data.lower():
    add_drop_idx = lower.index("add")
    alter_type = "add"
else:
    add_drop_idx = lower.index("drop column")
    alter_type = "drop"
table_name = input_data[len("alter table "): add_drop_idx].strip()
print("TABLE NAME:: ", table_name)
print("ALTER TYPE:: ", alter_type)

print("LOWER IS:: ", lower)

column_str = input_data[add_drop_idx + len("add"):].strip()
parts = column_str.split()
if len(parts) >= 2:
    column = parts[0]
    data_type = parts[1]
    print("COLUMN NAME::", column)
    print("DATA TYPE::", data_type)
else:
    print("ERROR: Invalid column definition")