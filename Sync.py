import json
import os
from datetime import datetime, timezone
from dateutil.parser import parse
from helper import *

# Function to get tasks from local JSON file
def get_local_tasks(file_path='tasks.json'):
    with open(file_path, 'r') as file:
        return json.load(file)

# Function to get last synced time from JSON file
def get_last_synced_time(file_path='last_synced_time.json'):
    try:
        with open(file_path, 'r') as file:
            return json.load(file)['last_synced_time']
    except (FileNotFoundError, KeyError):
        return None

# Function to save last synced time to JSON file
def save_last_synced_time(file_path='last_synced_time.json'):
    data = {'last_synced_time': datetime.now(timezone.utc).isoformat()}
    with open(file_path, 'w') as file:
        json.dump(data, file)

# Function to save tasks to local JSON file
def save_local_tasks(tasks, file_path='tasks.json'):
    with open(file_path, 'w') as file:
        json.dump(tasks, file, ensure_ascii=False, indent=2, default=str)

# Function to delete a task in Notion
def delete_notion_task(task_id):
    url = f'https://api.notion.com/v1/pages/{task_id}'
    try:
        response = requests.patch(url, headers=notion_headers, data=json.dumps({"archived": True}))
        response.raise_for_status()
        print(f"Task with ID {task_id} deleted successfully from Notion")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 400:
            print(f"Task with ID {task_id} not found in Notion, skipping deletion.")
        else:
            raise

# Function to delete a task in Todoist
def delete_todoist_task(task_id):
    url = f'https://api.todoist.com/rest/v2/tasks/{task_id}'
    try:
        response = requests.delete(url, headers=todoist_headers)
        response.raise_for_status()
        print(f"Task with ID {task_id} deleted successfully from Todoist")
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Task with ID {task_id} not found in Todoist, skipping deletion.")
        else:
            raise

# Function to create or update a task in Notion
def sync_notion_task(task):
    # Only sync if task was modified after last synced time
    last_synced_time = get_last_synced_time()
    if last_synced_time and task['last_modified'] <= last_synced_time:
        return

    url = f'https://api.notion.com/v1/pages/{task["notion-id"]}'
    payload = {
        'properties': {
            'Name': {'title': [{'text': {'content': task['name']}}]},
            'Done': {'checkbox': task['completed']},
            'Type': {'multi_select': [{'name': label} for label in task['labels']]}
        }
    }
    if task['due_date']:
        due_date_obj = parse(task['due_date'])
        if due_date_obj.time() != datetime.min.time():
            # If time is present, include it
            payload['properties']['Date'] = {'date': {'start': due_date_obj.isoformat()}}
        else:
            # If only date is present, format without time
            payload['properties']['Date'] = {'date': {'start': due_date_obj.strftime('%Y-%m-%d')}}
    else:
        payload['properties']['Date'] = {'date': None}

    response = requests.patch(url, headers=notion_headers, data=json.dumps(payload))
    response.raise_for_status()
    print(f"Task '{task['name']}' synced successfully to Notion")

# Function to create or update a task in Todoist
def sync_todoist_task(task):
    # Only sync if task was modified after last synced time
    last_synced_time = get_last_synced_time()
    if last_synced_time and task['last_modified'] <= last_synced_time:
        return

    url = f'https://api.todoist.com/rest/v2/tasks/{task["todoist-id"]}' if task['todoist-id'] else 'https://api.todoist.com/rest/v2/tasks'
    payload = {
        'content': task['name'],
        'labels': task['labels']
    }

    if task['due_date']:
        due_date_obj = parse(task['due_date'])
        if due_date_obj.time() != datetime.min.time():
            # If time is present, include it
            payload['due_string'] = due_date_obj.isoformat()
        else:
            # If only date is present, remove due_string
            payload['due_date'] = due_date_obj.strftime('%Y-%m-%d')
    else:
        payload['due_string'] = "no due date"

    try:
        if task['todoist-id']:
            # Update existing task
            response = requests.post(url, headers=todoist_headers, data=json.dumps(payload))
        else:
            # Create new task
            response = requests.post('https://api.todoist.com/rest/v2/tasks', headers=todoist_headers, data=json.dumps(payload))
        response.raise_for_status()
        print(f"Task '{task['name']}' synced successfully to Todoist")

        # Update the completed status separately
        if task['completed']:
            complete_todoist_task(response.json()['id'])
        else:
            reopen_todoist_task(response.json()['id'])
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Task with ID {task['todoist-id']} not found in Todoist, skipping sync.")
        else:
            raise
        
# Function to mark a task as completed in Todoist
def complete_todoist_task(task_id):
    url = f'https://api.todoist.com/rest/v2/tasks/{task_id}/close'
    try:
        response = requests.post(url, headers=todoist_headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Task with ID {task_id} not found in Todoist, skipping completion.")
        else:
            raise

# Function to reopen a task in Todoist
def reopen_todoist_task(task_id):
    url = f'https://api.todoist.com/rest/v2/tasks/{task_id}/reopen'
    try:
        response = requests.post(url, headers=todoist_headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            print(f"Task with ID {task_id} not found in Todoist, skipping reopening.")
        else:
            raise

# Main function to sync tasks from local JSON file to Notion and Todoist
def sync_local_tasks_to_notion_and_todoist():
    tasks = get_local_tasks()
    tasks_to_keep = []

    for task in tasks:
        if task.get('deleted', False):
            # Delete task from Notion and Todoist if marked as deleted
            if 'notion-id' in task:
                delete_notion_task(task['notion-id'])
            if 'todoist-id' in task:
                delete_todoist_task(task['todoist-id'])
        else:
            # Sync task to Notion and Todoist if not marked as deleted
            sync_notion_task(task)
            sync_todoist_task(task)
            tasks_to_keep.append(task)

    # Save the updated list of tasks to the local JSON file
    save_local_tasks(tasks_to_keep)

    # Save the last synced time after syncing all tasks
    save_last_synced_time()

# Run the sync function
sync_local_tasks_to_notion_and_todoist()
