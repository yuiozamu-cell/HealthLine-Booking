import mysql.connector

def main():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="clinic_appointment_db"
    )
    cursor = conn.cursor()

    try:
        # Create the junction table
        print("Creating employee_services table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_services (
                employee_id INT NOT NULL,
                service_id INT NOT NULL,
                PRIMARY KEY (employee_id, service_id)
            ) ENGINE=MyISAM DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)

        # Migrate existing data
        print("Migrating existing data...")
        cursor.execute("""
            INSERT IGNORE INTO employee_services (employee_id, service_id)
            SELECT id, service_id FROM employees WHERE service_id IS NOT NULL
        """)

        conn.commit()
        print("Migration successful!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    main()
