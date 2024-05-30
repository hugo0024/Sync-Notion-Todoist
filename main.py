import subprocess
import time

def run_script(script_name):
    """Run a Python script and wait for it to complete."""
    process = subprocess.run(["python", script_name], check=True)
    return process

def main():
    try:
        while True:
            # Run Notion_to_Local.py
            print("Running Notion_to_Local.py...")
            run_script("Notion_to_Local.py")
            time.sleep(4)
            
            # Run Todoist_to_Local.py
            print("Running Todoist_to_Local.py...")
            run_script("Todoist_to_Local.py")
            time.sleep(4)
            
    except KeyboardInterrupt:
        print("Exiting gracefully...")

if __name__ == "__main__":
    main()
