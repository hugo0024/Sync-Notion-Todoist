import requests
import json
import os
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

# Function to get tasks from Notion
def get_notion_tasks():
    url = f'https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query'
    response = requests.post(url, headers=notion_headers)
    
    if response.status_code == 401:
        print("Error: Invalid Notion API token. Please check your NOTION_API_TOKEN environment variable.")
        return []
    if response.status_code == 400:
        print("Error: Invalid Notion DataBase ID. Please check your NOTION_API_TOKEN environment variable.")
        return []
    
    response.raise_for_status()
    return response.json().get('results')

# Function to get tasks from Todoist
def get_todoist_tasks():
    url = 'https://api.todoist.com/rest/v2/tasks'
    response = requests.get(url, headers=todoist_headers)
    
    if response.status_code == 401:
        print("Error: Invalid Todoist API token. Please check your TODOIST_API_TOKEN environment variable.")
        return []
    
    response.raise_for_status()
    return response.json()

# Function to get completed tasks from Todoist
def get_completed_todoist_tasks():
    url = 'https://api.todoist.com/sync/v9/completed/get_all'
    response = requests.get(url, headers=todoist_headers)
    response.raise_for_status()
    return response.json().get('items', [])

# Function to create a task in Todoist
def create_todoist_task(task_name):
    existing_tasks = get_todoist_tasks()
    completed_tasks = get_completed_todoist_tasks()

    for task in existing_tasks:
        if task['content'] == task_name:
            print(f"Task '{task_name}' already exists in Todoist, skipping...")
            return task['id'], False

    for task in completed_tasks:
        if task['content'] == task_name:
            print(f"Task '{task_name}' is already completed in Todoist, skipping...")
            return task['task_id'], True

    url = 'https://api.todoist.com/rest/v2/tasks'
    payload = {
        'content': task_name
    }
    response = requests.post(url, headers=todoist_headers, data=json.dumps(payload))
    response.raise_for_status()
    print(f"Task '{task_name}' created successfully in Todoist")
    return response.json()['id'], False

# Function to save tasks to a local JSON file
def save_tasks_to_json(tasks, filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            existing_tasks = json.load(file)
    except FileNotFoundError:
        existing_tasks = []

    if tasks != existing_tasks:
        with open(filename, 'w', encoding='utf-8') as file:
            json.dump(tasks, file, ensure_ascii=False, indent=2)
        print(f"Update from Notion, tasks saved to {filename}")
        
        # Run Sync.py after saving the JSON data
        result = subprocess.run(["python", "Sync.py"], capture_output=True, text=True)
        if result.returncode == 0:
            print("Sync.py executed successfully.")
        else:
            print(f"Sync.py execution failed with error: {result.stderr}")
    else:
        print("No changes detected from Notion, skipping save.")

# Function to update the "ID" column of a Notion task with the Todoist task ID
def update_notion_task_id(notion_task_id, todoist_task_id):
    url = f'https://api.notion.com/v1/pages/{notion_task_id}'
    payload = {
        'properties': {
            'ID': {'number': int(todoist_task_id)}
        }
    }
    response = requests.patch(url, headers=notion_headers, data=json.dumps(payload))
    response.raise_for_status()

# Function to update the "Done" status of a Notion task
def update_notion_task_status(notion_task_id, completed):
    url = f'https://api.notion.com/v1/pages/{notion_task_id}'
    payload = {
        'properties': {
            'Done': {'checkbox': completed}
        }
    }
    response = requests.patch(url, headers=notion_headers, data=json.dumps(payload))
    response.raise_for_status()

# Function to load tasks from the JSON file
def load_tasks_from_json(filename):
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            tasks = json.load(file)
    except FileNotFoundError:
        tasks = []
    return tasks

# Main function
def sync_notion_to_json():
    notion_tasks = get_notion_tasks()

    if not notion_tasks:
        return

    tasks = load_tasks_from_json('tasks.json')
    tasks_dict = {task['notion-id']: task for task in tasks}

    notion_task_ids = set()

    for task in notion_tasks:
        task_id = task['id']
        notion_task_ids.add(task_id)
        task_name = task['properties']['Name']['title'][0]['text']['content']
        task_completed = task['properties']['Done']['checkbox']
        task_due_date = task['properties']['Date']['date']['start'] if task['properties']['Date']['date'] else None
        task_labels = [label['name'] for label in task['properties']['Type']['multi_select']]

        if task_id in tasks_dict:
            # Update existing task in JSON file
            task_data = tasks_dict[task_id]
            task_changed = False

            if task_data['name'] != task_name:
                task_data['name'] = task_name
                task_changed = True

            if task_data['completed'] != task_completed:
                task_data['completed'] = task_completed
                task_changed = True

            if task_data['due_date'] != task_due_date:
                task_data['due_date'] = task_due_date
                task_changed = True

            if set(task_data['labels']) != set(task_labels):
                task_data['labels'] = task_labels
                task_changed = True

            if task_changed:
                task_data['last_modified'] = datetime.now(timezone.utc).isoformat()

        else:
            # Create a task in Todoist and get the task ID
            todoist_task_id, is_completed = create_todoist_task(task_name)
            if todoist_task_id is None and is_completed:
                task_completed = True
                update_notion_task_status(task_id, True)
            elif todoist_task_id:
                update_notion_task_id(task_id, todoist_task_id)

            task_data = {
                'notion-id': task_id,
                'todoist-id': todoist_task_id,
                'name': task_name,
                'completed': task_completed,
                'due_date': task_due_date,
                'labels': task_labels,
                'last_modified': datetime.now(timezone.utc).isoformat()
            }

            tasks.append(task_data)

    # Mark tasks as deleted if they are not found in the Notion database
    for task in tasks:
        if task['notion-id'] not in notion_task_ids:
            task['deleted'] = True
            task['last_modified'] = datetime.now(timezone.utc).isoformat()

    save_tasks_to_json(tasks, 'tasks.json')

sync_notion_to_json()
