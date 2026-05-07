import mysql.connector
from app import get_db_connection

def alter_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Create service_categories table
        print("Creating service_categories table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS service_categories (
                id INT AUTO_INCREMENT PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                description TEXT
            )
        """)
        
        # 2. Add a default category if table is empty
        cursor.execute("SELECT COUNT(*) FROM service_categories")
        if cursor.fetchone()[0] == 0:
            print("Adding default 'General' category...")
            cursor.execute("INSERT INTO service_categories (name, description) VALUES ('General', 'General clinic services')")
            conn.commit()
            
        # 3. Alter services table to add category_id
        cursor.execute("SHOW COLUMNS FROM services LIKE 'category_id'")
        if not cursor.fetchone():
            print("Adding category_id column to services table...")
            # We add it as nullable first
            cursor.execute("ALTER TABLE services ADD COLUMN category_id INT")
            
            # Map existing services to the default 'General' category (ID 1)
            cursor.execute("UPDATE services SET category_id = 1 WHERE category_id IS NULL")
            conn.commit()
            
            # Now add the foreign key constraint
            cursor.execute("ALTER TABLE services ADD FOREIGN KEY (category_id) REFERENCES service_categories(id) ON DELETE CASCADE")
            
        conn.commit()
        print("Successfully updated the database schema for categories.")
        
    except Exception as e:
        print(f"Error updating database: {e}")
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals() and conn.is_connected():
            conn.close()

if __name__ == "__main__":
    alter_db()
