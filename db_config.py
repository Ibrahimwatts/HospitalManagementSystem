import mysql.connector

def create_connection():
    try:
        connection = mysql.connector.connect(
            host='127.0.0.1',
            user='root',  # Update with your MySQL username
            password='Ibrahimwatts5@',  # Update with your MySQL password
            database='hms_db'  # Update with your database name
        )
        if connection.is_connected():
            print("Successfully connected to the database!")
        return connection
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

def close_connection(connection):
    if connection and connection.is_connected():
        connection.close()
        print("Database connection closed.")

# Test the connection if this file is executed directly
if __name__ == "__main__":
    conn = create_connection()
    if conn:
        close_connection(conn)
