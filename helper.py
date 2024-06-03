import requests
import json
import os
import sys
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configuration
NOTION_API_TOKEN = os.getenv('NOTION_API_TOKEN')
NOTION_DATABASE_ID = os.getenv('NOTION_DATABASE_ID')
TODOIST_API_TOKEN = os.getenv('TODOIST_API_TOKEN')

notion_headers = {
    'Authorization': f'Bearer {NOTION_API_TOKEN}',
    'Content-Type': 'application/json',
    'Notion-Version': '2022-06-28'
}

todoist_headers = {
    'Authorization': f'Bearer {TODOIST_API_TOKEN}',
    'Content-Type': 'application/json'
}

# Function to clear the console
def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

# Function to get tasks from Notion
def get_notion_tasks():
    url = f'https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query'
    response = requests.post(url, headers=notion_headers)
    if response.status_code == 401:
        print("Error: Invalid Notion API token. Please check your NOTION_API_TOKEN environment variable.")
        sys.exit(1)
    if response.status_code == 400:
        print("Error: Invalid Notion Database ID. Please check your NOTION_DATABASE_ID environment variable.")
        sys.exit(2)
    
    response.raise_for_status()
    return response.json().get('results')

# Function to get tasks from Todoist
def get_todoist_tasks():
    url = 'https://api.todoist.com/rest/v2/tasks'
    response = requests.get(url, headers=todoist_headers)
    if response.status_code == 401:
        print("Error: Invalid Todoist API token. Please check your TODOIST_API_TOKEN environment variable.")
        sys.exit(3)
    response.raise_for_status()
    return response.json()

# Function to get completed tasks from Todoist
def get_completed_todoist_tasks():
    url = 'https://api.todoist.com/sync/v9/completed/get_all'
    response = requests.get(url, headers=todoist_headers)
    if response.status_code == 401:
        print("Error: Invalid Todoist API token. Please check your TODOIST_API_TOKEN environment variable.")
        sys.exit(3)
    response.raise_for_status()
    return response.json().get('items', [])

# Function to save tasks to the JSON file
def save_tasks_to_json(tasks, filename, name):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            existing_tasks = json.load(file)
    except FileNotFoundError:
        existing_tasks = []

    if tasks != existing_tasks:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(tasks, file, ensure_ascii=False, indent=2, default=str)
        print(f"Update from " + name + ", tasks saved to " + filename + ".")
        # Run Sync.py after saving the JSON data
        result = subprocess.run(["python", "Sync.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Sync.py executed successfully.")
        else:
            print(f"Sync.py execution failed with error: {result.stderr}")
    else:
        print(f"No changes detected from " + name)


# Function to load tasks from the JSON file
def load_tasks_from_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            tasks = json.load(file)
    except FileNotFoundError:
        tasks = []
    # Ensure all tasks have the 'deleted' field
    for task in tasks:
        if 'deleted' not in task:
            task['deleted'] = False
    return tasks