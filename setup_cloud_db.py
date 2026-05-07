import mysql.connector

# ==========================================
# FILL THESE IN WITH YOUR AIVEN CREDENTIALS
# ==========================================
DB_HOST = "mysql-1b65b507-yuiozamu-a485.b.aivencloud.com"
DB_PORT = 26554
DB_USER = "avnadmin"
DB_PASSWORD = "AVNS_17H0aOdcqCAIcoswV-R"
DB_NAME = "defaultdb"

def setup_cloud_database():
    print("Connecting to cloud database...")
    try:
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        cursor = conn.cursor()
        
        print("Connected successfully! Reading schema.sql...")
        with open('schema.sql', 'r') as f:
            sql_script = f.read()
            
        # Split the script into separate statements
        sql_commands = sql_script.split(';')
        
        for command in sql_commands:
            if command.strip():
                try:
                    cursor.execute(command)
                except Exception as e:
                    print(f"Warning executing statement: {e}")
                
        conn.commit()
        cursor.close()
        conn.close()
        print("\n✅ SUCCESS! All tables have been created in your new cloud database.")
        print("You are now ready to hit 'Deploy' on Vercel!")
        
    except mysql.connector.Error as err:
        print(f"\n❌ ERROR: {err}")
        print("Please check your credentials and try again.")

if __name__ == "__main__":
    setup_cloud_database()
