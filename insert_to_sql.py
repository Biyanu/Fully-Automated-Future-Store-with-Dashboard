import requests
import psycopg2
import json
from datetime import datetime
from dotenv import load_dotenv
import os

# os.chdir(r"D:\MSBA\Courses\Fall_2024\BZAN545\Assignments\Group_ASS\final_project\python_code")
# os.getcwd()

load_dotenv()

# Get credentials from environment variables
db_host = os.getenv('DB_HOST')
db_name = os.getenv('DB_NAME')
db_user = os.getenv('DB_USER')
db_password = os.getenv('DB_PASSWORD')

def get_db_connection():
    """Establish a connection to PostgreSQL."""
    return psycopg2.connect(
        dbname=db_name, user=db_user, password=db_password, host=db_host
    )

def fetch_data_from_api(api_url):
    """Fetch JSON data from the API."""
    response = requests.get(api_url)
    response.raise_for_status()  # Raise an error if the request fails
    return response.json()

def format_date(date_str):
    """Format the date to match PostgreSQL format."""
    return datetime.strptime(date_str, "%m/%d/%Y").strftime("%Y-%m-%d")

def create_table_if_not_exists(cur):
    """Create the table if it does not exist."""
    create_table_sql = """
    drop table if exists feature_store;
    CREATE TABLE IF NOT EXISTS feature_store (
        salesdate DATE,
        productid INT,
        region text,
        freeship BOOLEAN,
        discount FLOAT,
        itemssold INT,
        update_time TIMESTAMP
    );
    """
    cur.execute(create_table_sql)

def load_data_to_db(data):
    """Insert JSON data into PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Create table if not exists
        create_table_if_not_exists(cur)

        for item in data:
            salesdate = format_date(item['salesdate'])
            # Explicitly convert freeship to a boolean (1 becomes TRUE, 0 becomes FALSE)
            freeship = True if item['freeship'] == 1 else False
            
            # Insert data into the table
            cur.execute(
                """
                INSERT INTO feature_store (salesdate, productid, region, freeship, discount, itemssold, update_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    salesdate, 
                    item['productid'], 
                    item['region'],
                    freeship,  
                    item['discount'], 
                    item['itemssold'], 
                    item['update_time']
                )
            )
        conn.commit()
        print("Data loaded successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Failed to load data: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    api_url = "http://127.0.0.1:5000/data" 
    data = fetch_data_from_api(api_url)
    load_data_to_db(data)
