
# importing libraries 
import datetime as dt
from datetime import datetime, timedelta, timezone
import pandas as pd
import schedule
import requests
import datetime as dt 
import time
import requests
import sqlalchemy
import os
import logging

'''######################################################'''
''''complete code is written int the lines below'''

import logging
import os
import pandas as pd
import requests
from datetime import datetime as dt
from datetime import timezone, timedelta

logging.basicConfig(filename= 'D:\\MSBA\\Courses\\Fall_2024\\BZAN545\\Assignments\\Group_ASS\\final_project\\data_sets\\feature_store_log.log', level=logging.INFO)

# Function to fetch data from URL
def fetch_data():
    try:
        url = 'http://ballings.co/data.py'
        response = requests.get(url)
        if response.status_code == 200:
            # Execute the fetched content in a safe way
            local_vars = {}
            exec(response.content, {}, local_vars)
            data = local_vars.get('data')
            if data is None:
                raise ValueError("The variable 'data' was not defined in the script.")
            return pd.DataFrame(data)  # Convert data to DataFrame
        else:
            raise ValueError(f"Failed to fetch data, HTTP status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Failed to fetch data: {e}")
        raise

# Function to save new rows to local disk
def save_data_daily(new_rows):
    directory = r"D:\\MSBA\\Courses\\Fall_2024\\BZAN545\\Assignments\\Group_ASS\\final_project\\data_sets"
    os.makedirs(directory, exist_ok=True)  # Create directory if it doesn't exist

    file_path = os.path.join(directory, "feature_store.csv")

    # Load existing data if file exists
    if os.path.exists(file_path):
        existing_data = pd.read_csv(file_path)
    else:
        existing_data = pd.DataFrame()

    # Find new rows that are not in the existing data based on specific key columns
    if not existing_data.empty:
        # Assuming 'salesdate', 'productid', and 'region' uniquely identify a record
        existing_keys = existing_data[['salesdate', 'productid', 'region']]
        new_keys = new_rows[['salesdate', 'productid', 'region']]
        
        # Identify new rows by checking for their keys
        new_rows = new_rows[~new_keys.apply(tuple, axis=1).isin(existing_keys.apply(tuple, axis=1))]

    # Add update_time to new rows if any
    if not new_rows.empty:
        eastern_time = timezone(timedelta(hours=-5)) 
        new_rows['update_time'] = dt.now(eastern_time).strftime("%Y-%m-%d %I:%M %p")  # Format the update time

        # Append new rows to existing data
        updated_data = pd.concat([existing_data, new_rows], ignore_index=True)
    else:
        updated_data = existing_data

    # Save the updated data
    updated_data.to_csv(file_path, index=False)
    logging.info(f"Data saved to {file_path}")

# Main update function to fetch and save data
def daily_update():
    try:
        new_data = fetch_data()          # Fetch the new data
        save_data_daily(new_data)        # Save it to disk only new rows
        logging.info(f"Feature store updated successfully at {dt.now()}")
    except Exception as e:
        logging.error(f"Failed to update feature store: {e}")

# Run the updater once for testing purposes
if __name__ == "__main__":
    logging.info("Starting the daily feature store updater...")
    daily_update()  # Run update once for testing
