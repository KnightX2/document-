import mysql.connector
from mysql.connector import Error

def update_document_table():
    try:
        # Connect to MySQL
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='',
            database='document_archive'
        )
        
        if connection.is_connected():
            cursor = connection.cursor()
            
            # Check if table exists
            cursor.execute("SHOW TABLES LIKE 'document'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # Create table if it doesn't exist
                create_table_query = """
                CREATE TABLE document (
                    ID INT AUTO_INCREMENT PRIMARY KEY,
                    DocumentID VARCHAR(50) NOT NULL UNIQUE,
                    Title VARCHAR(255) NOT NULL,
                    DocumentName VARCHAR(255),
                    DocumentType VARCHAR(50),
                    Date DATE,
                    EntityType VARCHAR(50),
                    Description TEXT,
                    FromSection VARCHAR(100),
                    CurrentSection VARCHAR(100),
                    FilePath VARCHAR(500),
                    IsVisible BOOLEAN DEFAULT TRUE,
                    CreatedBy VARCHAR(100),
                    CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                )
                """
                cursor.execute(create_table_query)
                print("Document table created successfully!")
            else:
                # Check existing columns and add missing ones
                cursor.execute("DESCRIBE document")
                existing_columns = [column[0] for column in cursor.fetchall()]
                
                # Define required columns
                required_columns = {
                    'DocumentName': 'VARCHAR(255)',
                    'DocumentType': 'VARCHAR(50)',
                    'EntityType': 'VARCHAR(50)',
                    'Description': 'TEXT',
                    'FromSection': 'VARCHAR(100)',
                    'CurrentSection': 'VARCHAR(100)',
                    'FilePath': 'VARCHAR(500)',
                    'IsVisible': 'BOOLEAN DEFAULT TRUE',
                    'CreatedAt': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
                    'UpdatedAt': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP'
                }
                
                # Add missing columns
                for column_name, column_type in required_columns.items():
                    if column_name not in existing_columns:
                        try:
                            alter_query = f"ALTER TABLE document ADD COLUMN {column_name} {column_type}"
                            cursor.execute(alter_query)
                            print(f"Added column: {column_name}")
                        except Error as e:
                            print(f"Error adding column {column_name}: {e}")
                
                # Update existing columns if needed
                if 'Department' in existing_columns and 'CurrentSection' not in existing_columns:
                    try:
                        cursor.execute("ALTER TABLE document CHANGE COLUMN Department CurrentSection VARCHAR(100)")
                        print("Renamed Department column to CurrentSection")
                    except Error as e:
                        print(f"Error renaming Department column: {e}")
                
                if 'Address' in existing_columns and 'Description' not in existing_columns:
                    try:
                        cursor.execute("ALTER TABLE document CHANGE COLUMN Address Description TEXT")
                        print("Renamed Address column to Description")
                    except Error as e:
                        print(f"Error renaming Address column: {e}")
            
            connection.commit()
            print("Database schema updated successfully!")
            
    except Error as e:
        print(f"Error: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()
            print("Database connection closed.")

if __name__ == "__main__":
    update_document_table() 