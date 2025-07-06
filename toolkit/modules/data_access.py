import sqlite3
import os
import json  # For more complex data types if necessary, though SQL results are usually lists of tuples

# Assuming the ToolkitModule interface is defined or will be defined in a central place.
# from toolkit.core.module_base import ToolkitModule


class ToolkitModule:  # Placeholder for the actual base class from architecture
    def get_name(self) -> str:
        raise NotImplementedError

    def get_description(self) -> str:
        raise NotImplementedError

    def execute(self, context: dict, **kwargs) -> dict:
        raise NotImplementedError


class DataAccessModule(ToolkitModule):
    def get_name(self) -> str:
        return "data_access"

    def get_description(self) -> str:
        return "Executes SQL queries on a specified SQLite database."

    def execute(
        self, context: dict, db_path: str, query: str, parameters: tuple = None
    ) -> dict:
        """
        Executes a SQL query on the given SQLite database.

        :param context: Dictionary for shared context (not used in this basic version).
        :param db_path: Path to the SQLite database file.
        :param query: The SQL query to execute.
        :param parameters: Optional tuple of parameters for the SQL query.
        :return: Dictionary containing the results or an error.
        """
        if not os.path.exists(db_path):
            return {"error": f"Database file not found: {db_path}"}

        if not query.strip():
            return {"error": "Query cannot be empty."}

        # For safety, generally only allow SELECT statements unless explicitly stated.
        # This is a basic check; a more robust solution might involve parsing the SQL
        # or having different methods for read/write operations.
        if not query.lstrip().upper().startswith("SELECT"):
            # Allowing PRAGMA for table info, etc.
            if not query.lstrip().upper().startswith("PRAGMA"):
                return {
                    "error": "Only SELECT or PRAGMA queries are allowed in this basic version."
                }

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            if parameters:
                cursor.execute(query, parameters)
            else:
                cursor.execute(query)

            # For SELECT queries, fetch results. For others, commit if needed (not for SELECT).
            if query.lstrip().upper().startswith(
                "SELECT"
            ) or query.lstrip().upper().startswith("PRAGMA"):
                column_names = (
                    [description[0] for description in cursor.description]
                    if cursor.description
                    else []
                )
                rows = cursor.fetchall()
                conn.close()
                return {
                    "db_path": db_path,
                    "query": query,
                    "columns": column_names,
                    "row_count": len(rows),
                    "rows": rows,
                }
            else:
                # This part won't be reached due to the safety check above for this basic version.
                # If we were to allow INSERT/UPDATE/DELETE:
                # conn.commit()
                # affected_rows = cursor.rowcount
                conn.close()
                return {
                    "db_path": db_path,
                    "query": query,
                    "message": "Query executed (non-SELECT operations are restricted in this version).",
                    # "affected_rows": affected_rows
                }

        except sqlite3.Error as e:
            return {"error": f"Database error: {str(e)}", "query": query}
        except Exception as e:
            return {"error": f"An unexpected error occurred: {str(e)}", "query": query}


# Example usage (for testing this module directly)
if __name__ == "__main__":
    data_module = DataAccessModule()
    print(f"Testing module: {data_module.get_name()} - {data_module.get_description()}")

    # Create a dummy DB for testing
    TEST_DB_PATH = "test_example.db"
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

    conn = sqlite3.connect(TEST_DB_PATH)
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    cursor.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("Alice Wonderland", "alice@example.com"),
    )
    cursor.execute(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("Bob The Builder", "bob@example.com"),
    )
    conn.commit()
    conn.close()

    print("\n--- Test 1: Valid SELECT query ---")
    results1 = data_module.execute(
        context={},
        db_path=TEST_DB_PATH,
        query="SELECT id, name FROM users WHERE id = ?",
        parameters=(1,),
    )
    print(json.dumps(results1, indent=2))

    print("\n--- Test 2: Valid SELECT query (all users) ---")
    results2 = data_module.execute(
        context={}, db_path=TEST_DB_PATH, query="SELECT * FROM users"
    )
    print(json.dumps(results2, indent=2))

    print("\n--- Test 3: PRAGMA query ---")
    results_pragma = data_module.execute(
        context={}, db_path=TEST_DB_PATH, query="PRAGMA table_info(users);"
    )
    print(json.dumps(results_pragma, indent=2))

    print("\n--- Test 4: Non-SELECT query (should be blocked) ---")
    results3 = data_module.execute(
        context={},
        db_path=TEST_DB_PATH,
        query="INSERT INTO users (name, email) VALUES ('Charlie', 'charlie@example.com')",
    )
    print(json.dumps(results3, indent=2))

    print("\n--- Test 5: Query on non-existent DB ---")
    results4 = data_module.execute(
        context={}, db_path="non_existent.db", query="SELECT * FROM users"
    )
    print(json.dumps(results4, indent=2))

    print("\n--- Test 6: Empty query ---")
    results5 = data_module.execute(context={}, db_path=TEST_DB_PATH, query="  ")
    print(json.dumps(results5, indent=2))

    print("\n--- Test 7: SQL syntax error ---")
    results_syntax_error = data_module.execute(
        context={}, db_path=TEST_DB_PATH, query="SELECT FROMM users"
    )
    print(json.dumps(results_syntax_error, indent=2))

    # Clean up dummy DB
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
