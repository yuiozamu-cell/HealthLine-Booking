import mysql.connector

def alter_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="clinic_appointment_db"
        )
        cursor = conn.cursor()

        # Add end_time to employee_schedules
        try:
            cursor.execute("ALTER TABLE employee_schedules ADD COLUMN end_time TIME NOT NULL DEFAULT '00:00:00'")
            print("Added end_time to employee_schedules")
        except mysql.connector.Error as e:
            print(f"Skipped employee_schedules (might already exist): {e}")

        # Add end_time to appointments
        try:
            cursor.execute("ALTER TABLE appointments ADD COLUMN end_time TIME NOT NULL DEFAULT '00:00:00'")
            print("Added end_time to appointments")
        except mysql.connector.Error as e:
            print(f"Skipped appointments (might already exist): {e}")

        # Add requested_end_time to appointment_requests
        try:
            cursor.execute("ALTER TABLE appointment_requests ADD COLUMN requested_end_time TIME NULL")
            print("Added requested_end_time to appointment_requests")
        except mysql.connector.Error as e:
            print(f"Skipped appointment_requests (might already exist): {e}")

        conn.commit()
        print("Database alterations completed successfully.")

    except mysql.connector.Error as err:
        print(f"Error connecting to MySQL: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    alter_db()
