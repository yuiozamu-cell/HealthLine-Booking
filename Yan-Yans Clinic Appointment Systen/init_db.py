import mysql.connector

def init_db():
    try:
        # Connect to MySQL server without specifying a database first
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password=""
        )
        cursor = conn.cursor()

        # Read schema.sql
        with open('schema.sql', 'r') as file:
            sql_script = file.read()

        # Split script into individual statements
        statements = sql_script.split(';')

        print("Initializing database...")
        for statement in statements:
            if statement.strip():
                try:
                    cursor.execute(statement)
                except mysql.connector.Error as err:
                    print(f"Error executing statement: {err}")

        conn.commit()
        print("Database initialized successfully.")

    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    init_db()
