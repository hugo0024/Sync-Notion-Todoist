import subprocess
import time
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
import threading
import os
from dotenv import load_dotenv

def check_env_variables():
    load_dotenv()  # Load environment variables from .env file
    
    notion_api_token = os.getenv("NOTION_API_TOKEN")
    notion_database_id = os.getenv("NOTION_DATABASE_ID")
    todoist_api_token = os.getenv("TODOIST_API_TOKEN")
    
    if not notion_api_token or not notion_database_id or not todoist_api_token:
        window = tk.Tk()
        window.title("Enter API Keys")
        
        frame = ttk.Frame(window, padding="10")
        frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        ttk.Label(frame, text="Notion API Token:").grid(row=0, column=0, sticky=tk.W)
        notion_api_token_entry = ttk.Entry(frame, width=40)
        notion_api_token_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Notion Database ID:").grid(row=1, column=0, sticky=tk.W)
        notion_database_id_entry = ttk.Entry(frame, width=40)
        notion_database_id_entry.grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(frame, text="Todoist API Token:").grid(row=2, column=0, sticky=tk.W)
        todoist_api_token_entry = ttk.Entry(frame, width=40)
        todoist_api_token_entry.grid(row=2, column=1, padx=5, pady=5)
        
        def save_keys():
            notion_api_token = notion_api_token_entry.get()
            notion_database_id = notion_database_id_entry.get()
            todoist_api_token = todoist_api_token_entry.get()
            
            with open(".env", "w") as file:
                file.write(f'NOTION_API_TOKEN="{notion_api_token}"\n')
                file.write(f'NOTION_DATABASE_ID="{notion_database_id}"\n')
                file.write(f'TODOIST_API_TOKEN="{todoist_api_token}"\n')
            
            window.destroy()
        
        ttk.Button(frame, text="Save", command=save_keys).grid(row=3, column=0, columnspan=2, padx=5, pady=5)
        
        window.mainloop()

def run_script(script_name, output_widget):
    """Run a Python script and display its output in the GUI."""
    try:
        process = subprocess.Popen(["python", script_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                output_widget.insert(tk.END, output)
                output_widget.see(tk.END)  # Scroll to the bottom
                output_widget.update_idletasks()  # Update the GUI
        return process.poll()
    except subprocess.CalledProcessError as e:
        if e.returncode == 1:
            output_widget.insert(tk.END, "Error: Invalid Notion API token. Please check your NOTION_API_TOKEN environment variable.\n")
        elif e.returncode == 2:
            output_widget.insert(tk.END, "Error: Invalid Notion Database ID. Please check your NOTION_DATABASE_ID environment variable.\n")
        elif e.returncode == 3:
            output_widget.insert(tk.END, "Error: Invalid Todoist API token. Please check your TODOIST_API_TOKEN environment variable.\n")
        return None

def start_services(output_widget):
    try:
        # Run Notion_to_Local.py
        output_widget.insert(tk.END, "Running Notion_to_Local.py...\n")
        result = run_script("Notion_to_Local.py", output_widget)
        if result is None:
            return
        time.sleep(4)
        
        # Run Todoist_to_Local.py
        output_widget.insert(tk.END, "Running Todoist_to_Local.py...\n")
        result = run_script("Todoist_to_Local.py", output_widget)
        if result is None:
            return
        time.sleep(4)
        
    except KeyboardInterrupt:
        output_widget.insert(tk.END, "Exiting gracefully...\n")

def create_gui():
    window = tk.Tk()
    window.title("Sync Notion and Todoist")
    
    frame = ttk.Frame(window, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    output_widget = ScrolledText(frame, height=20, width=60)
    output_widget.grid(row=0, column=0, padx=5, pady=5)
    
    def start_services_thread():
        thread = threading.Thread(target=start_services, args=(output_widget,))
        thread.start()
    
    start_button = ttk.Button(frame, text="Start", command=start_services_thread)
    start_button.grid(row=1, column=0, padx=5, pady=5)
    
    window.mainloop()

if __name__ == "__main__":
    check_env_variables()
    create_gui()