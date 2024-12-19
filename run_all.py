
import subprocess
import time
import requests
import threading
import os

os.chdir(r"D:\MSBA\Courses\Fall_2024\BZAN545\Assignments\Group_ASS\final_project\python_code")
os.getcwd()

def run_script(script_name, step_description, wait_time=1):
  
    print(f"Step: {step_description} - Starting...")
    
    # Wait before starting the script
    time.sleep(wait_time)  # Wait before running the script
    
    try:
        print(f"Running {script_name}...")
        result = subprocess.run(['python', script_name], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"{script_name} executed successfully.")
        print(result.stdout.decode())  
    except subprocess.CalledProcessError as e:
        print(f"Error occurred while running {script_name}: {e.stderr.decode()}")
        exit(1)  
    
    # Wait after the script completes
    print(f"Step: {step_description} - Completed.\n")
    time.sleep(5)  # Wait after running the script

def run_flask_in_thread(script_name):
    """Run Flask API in a separate thread and wait until it's accessible."""
    def target():
        subprocess.run(['python', script_name])

    print("Step: Running Flask API in the background...")
    thread = threading.Thread(target=target)
    thread.daemon = True  # Ensure the thread exits when the main program exits
    thread.start()

    # Check if the API is accessible
    for _ in range(10):  # Retry 10 times (adjust as needed)
        try:
            response = requests.get('http://127.0.0.1:5000/data')  # Test endpoint
            if response.status_code == 200:
                print("Flask API is up and running!")
                return thread
        except requests.ConnectionError:
            time.sleep(8)  # Wait 2 seconds before retrying

    print("Failed to connect to the Flask API.")
    exit(1)

def automate_process():
    """Automates the execution of fetch.py, api.py, sql.py, and dash.py in sequence."""
    print("Starting the entire data pipeline process...\n")

    # Fetching data from remote server
    run_script('fetch_data.py', "Fetching data from the remote server...", wait_time=5)
    
    # Running the Flask API
    flask_thread = run_flask_in_thread('pro_flask_api.py')  # Start Flask API in thread
    time.sleep(10)  # Allow extra time for Flask to spin up

    # Inserting data into SQL
    run_script('insert_to_sql.py', "Inserting the fetched data into the SQL database...", wait_time=3)
    
    # Running the dashboard
    run_script('dashboard.py', "Running the dashboard to visualize the data...", wait_time=1)

    print("Automation process completed successfully. All steps are done!")

if __name__ == "__main__":
    automate_process()
