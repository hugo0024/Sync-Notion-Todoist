import json
import os
import subprocess
from datetime import datetime, timezone, timedelta
from helper import *
import requests
import pytz

# Define the GMT+8 timezone
GMT_PLUS_8 = pytz.timezone('Etc/GMT-8')

# Function to create a task in Notion
def create_notion_task(task_name, task_description, task_due_date, todoist_task_id, notion_tasks_id_dict, task_labels):
    # Check if a task with the same ID already exists
    if int(todoist_task_id) in notion_tasks_id_dict:
        print(f"Task '{task_name}' already exists in Notion, skipping...")
        return

    url = 'https://api.notion.com/v1/pages'
    payload = {
        'parent': {'database_id': NOTION_DATABASE_ID},
        'properties': {
            'Name': {'title': [{'text': {'content': task_name}}]},
            'Done': {'checkbox': False},
            'ID': {'number': int(todoist_task_id)},
            'Type': {'multi_select': [{'name': label} for label in task_labels]}
        }
    }
    if task_due_date:
        due_date_obj = datetime.fromisoformat(task_due_date)
        if due_date_obj.tzinfo is None:
            # Assume the local time is in a specific timezone, e.g., GMT+08:00
            local_tz = GMT_PLUS_8
            due_date_obj = local_tz.localize(due_date_obj)
        task_due_date = due_date_obj.astimezone(GMT_PLUS_8).strftime('%Y-%m-%dT%H:%M:%S%z')
        # Adjust the format to include the colon in the timezone offset
        task_due_date = task_due_date[:-2] + ':' + task_due_date[-2:]
        payload['properties']['Date'] = {'date': {'start': task_due_date}}
    
    response = requests.post(url, headers=notion_headers, data=json.dumps(payload))
    response.raise_for_status()
    print(f"Task '{task_name}' created successfully in Notion")

def sync_todoist_to_json():
    tasks = load_tasks_from_json('tasks.json')
    todoist_tasks = get_todoist_tasks()
    completed_todoist_tasks = get_completed_todoist_tasks()
    notion_tasks = get_notion_tasks()

    # Create dictionaries for quick lookups
    tasks_dict = {int(task['todoist-id']): task for task in tasks}
    notion_tasks_id_dict = {task['properties']['ID']['number']: task for task in notion_tasks if 'ID' in task['properties'] and 'number' in task['properties']['ID']}
    todoist_tasks_dict = {int(task['id']): task for task in todoist_tasks}
    completed_todoist_tasks_dict = {int(task['task_id']): task for task in completed_todoist_tasks}

    # Create new Notion tasks for Todoist tasks that don't exist in Notion
    for todoist_task in todoist_tasks:
        task_name = todoist_task['content']
        task_description = todoist_task.get('description', '')
        todoist_task_id = int(todoist_task['id'])
        todoist_task_labels = todoist_task['labels']
        if todoist_task_id not in notion_tasks_id_dict:
            due = todoist_task.get('due')
            task_due_date = due.get('datetime') if due and 'datetime' in due else due.get('date') if due else ''
            if task_due_date:
                # Convert to GMT+8 if necessary
                due_date_obj = datetime.fromisoformat(task_due_date)
                if due_date_obj.tzinfo is None:
                    # Assume the local time is in a specific timezone, e.g., GMT+08:00
                    local_tz = GMT_PLUS_8
                    due_date_obj = local_tz.localize(due_date_obj)
                task_due_date = due_date_obj.astimezone(GMT_PLUS_8).strftime('%Y-%m-%dT%H:%M:%S%z')
                # Adjust the format to include the colon in the timezone offset
                task_due_date = task_due_date[:-2] + ':' + task_due_date[-2:]
            create_notion_task(task_name, task_description, task_due_date, todoist_task_id, notion_tasks_id_dict, todoist_task_labels)

    # Update local JSON file based on Todoist tasks
    for task in tasks:
        todoist_task_id = int(task['todoist-id'])
        task_changed = False

        if todoist_task_id in completed_todoist_tasks_dict:
            if not task['completed']:
                task['completed'] = True
                task_changed = True
        elif todoist_task_id in todoist_tasks_dict:
            todoist_task = todoist_tasks_dict[todoist_task_id]
            if task['completed']:
                task['completed'] = False
                task_changed = True
            if task['name'] != todoist_task['content']:
                task['name'] = todoist_task['content']
                task_changed = True
            
            # Check if 'due' attribute exists and is not None
            if 'due' in todoist_task and todoist_task['due'] is not None:
                due = todoist_task['due']
                due_date = due.get('datetime') if 'datetime' in due else due.get('date', '')
                if due_date:
                    due_date_obj = datetime.fromisoformat(due_date)
                    if due_date_obj.tzinfo is None:
                        # Assume the local time is in a specific timezone, e.g., GMT+08:00
                        local_tz = GMT_PLUS_8
                        due_date_obj = local_tz.localize(due_date_obj)
                    due_date = due_date_obj.astimezone(GMT_PLUS_8).strftime('%Y-%m-%dT%H:%M:%S%z')
                    # Adjust the format to include the colon in the timezone offset
                    due_date = due_date[:-2] + ':' + due_date[-2:]
                if task['due_date'] != due_date:
                    task['due_date'] = due_date
                    task_changed = True
            else:
                if task['due_date'] is not None:
                    task['due_date'] = None
                    task_changed = True
        
            if set(task['labels']) != set(todoist_task['labels']):
                task['labels'] = todoist_task['labels']
                task_changed = True

        # Mark task as deleted if it no longer exists in Todoist
        if todoist_task_id not in todoist_tasks_dict and todoist_task_id not in completed_todoist_tasks_dict:
            if not task['deleted']:
                task['deleted'] = True
                task_changed = True

        # Update the last_modified timestamp if the task has changed
        if task_changed:
            task['last_modified'] = datetime.now(timezone.utc).isoformat()

    save_tasks_to_json(tasks, 'tasks.json')

sync_todoist_to_json()