
# Sync-Notion-Todoist
This application, Sync-Notion-Todoist, is designed to provide a two-way synchronization between your Notion database and Todoist tasks. It allows you to manage your tasks seamlessly across both platforms.

# Features
- Fetch tasks from Notion and Todoist.
- Create and delete tasks in Todoist based on your Notion databse tasks.
- Create and delete tasks in Notion database based on your Todoist tasks.
- Update task on both Todoist and Notion database
- Automatically sync tasks whenever there are changes in Notion or Todoist.

# How it Works
The application uses the APIs provided by both Notion and Todoist to fetch and manipulate tasks. It compares the tasks from both platforms and performs necessary updates to keep them in sync.

# Setup
1. Clone the repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt`
3. Create a *.env* file in the root directory to include your Notion API tonken, Todoist API tonken and Notion databse ID in the following format:

        NOTION_API_TOKEN = "YOUR_NOTION_API_TOKEN"
	    NOTION_DATABASE_ID = "YOUR_NOTION_DATABASE_ID"
	    TODOIST_API_TOKEN = "YOUR_TODOIST_API_TOKEN"
4. Run `main.py`
