import subprocess
import time

def run_script(script_name):
    """Run a Python script and print its output in real-time."""
    try:
        process = subprocess.Popen(["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
        return process.poll()
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            print("Error: Invalid Notion API token. Please check your NOTION_API_TOKEN environment variable.")
        elif e.returncode == 2:
            print("Error: Invalid Notion Database ID. Please check your NOTION_DATABASE_ID environment variable.")
        elif e.returncode == 3:
            print("Error: Invalid Todoist API token. Please check your TODOIST_API_TOKEN environment variable.")
        return None

def main():
    try:
        while True:
            # Run Notion_to_Local.py
            print("Running Notion_to_Local.py...")
            result = run_script("Notion_to_Local.py")
            if result is None:
                break
            time.sleep(4)
            
            # Run Todoist_to_Local.py
            print("Running Todoist_to_Local.py...")
            result = run_script("Todoist_to_Local.py")
            if result is None:
                break
            time.sleep(4)
            
    except KeyboardInterrupt:
        print("Exiting gracefully...")

if __name__ == "__main__":
    main()