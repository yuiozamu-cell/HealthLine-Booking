import mysql.connector

def update_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="clinic_appointment_db"
        )
        cursor = conn.cursor()

        # Drop old employee_slots
        cursor.execute("DROP TABLE IF EXISTS employee_slots")

        # Create new employee_schedules
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_schedules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id INT NOT NULL,
                day_of_week ENUM('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday') NOT NULL,
                time TIME NOT NULL,
                FOREIGN KEY (employee_id) REFERENCES employees(id) ON DELETE CASCADE,
                UNIQUE(employee_id, day_of_week, time)
            )
        """)

        # Drop and recreate appointment_requests
        cursor.execute("DROP TABLE IF EXISTS appointment_requests")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointment_requests (
                id INT AUTO_INCREMENT PRIMARY KEY,
                appointment_id INT NOT NULL,
                request_type ENUM('Reschedule', 'Cancel') NOT NULL DEFAULT 'Reschedule',
                requested_date DATE NULL,
                requested_time TIME NULL,
                status ENUM('Pending', 'Approved', 'Rejected') DEFAULT 'Pending',
                FOREIGN KEY (appointment_id) REFERENCES appointments(id) ON DELETE CASCADE
            )
        """)

        conn.commit()
        print("Database updated successfully.")

    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    update_db()
