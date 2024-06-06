import json
import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from helper import *

# Define the GMT+8 timezone
GMT_PLUS_8 = timezone(timedelta(hours=8))

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

        if task_due_date:
            # Remove milliseconds from the due date and localize to GMT+8
            task_due_date = datetime.fromisoformat(task_due_date).replace(microsecond=0).astimezone(GMT_PLUS_8).isoformat()

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
                task_data['last_modified'] = datetime.now(timezone.utc).astimezone(GMT_PLUS_8).isoformat()

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
                'last_modified': datetime.now(timezone.utc).astimezone(GMT_PLUS_8).isoformat()
            }

            tasks.append(task_data)

    # Mark tasks as deleted if they are not found in the Notion database
    for task in tasks:
        if task['notion-id'] not in notion_task_ids:
            task['deleted'] = True
            task['last_modified'] = datetime.now(timezone.utc).astimezone(GMT_PLUS_8).isoformat()

    save_tasks_to_json(tasks, 'tasks.json', "Notion")

sync_notion_to_json()