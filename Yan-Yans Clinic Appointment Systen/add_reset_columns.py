import mysql.connector
from app import get_db_connection

def add_reset_columns():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if columns already exist to prevent errors if run multiple times
        cursor.execute("SHOW COLUMNS FROM users LIKE 'reset_code'")
        if not cursor.fetchone():
            print("Adding reset_code column...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_code VARCHAR(10) NULL")
            
        cursor.execute("SHOW COLUMNS FROM users LIKE 'reset_code_expiry'")
        if not cursor.fetchone():
            print("Adding reset_code_expiry column...")
            cursor.execute("ALTER TABLE users ADD COLUMN reset_code_expiry DATETIME NULL")
            
        conn.commit()
        print("Successfully updated the users table.")
        
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    add_reset_columns()
