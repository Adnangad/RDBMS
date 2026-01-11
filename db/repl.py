from engine import engine

def main():
    print("Mini RDBMS REPL")
    print("Allowed data types: DECIMAL, FLOAT, VARCHAR, INT, TEXT, BOOL")
    print("Type 'exit' or 'quit' to leave.\n")

    while True:
        user_input = input("rdbms> ")

        if not user_input.strip():
            continue

        if user_input.strip().lower() in ("exit", "quit"):
            print("Goodbye 👋")
            break

        result = engine(user_input)
        print("System:", result)


main()
