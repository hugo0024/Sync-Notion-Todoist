


# Sync Notion Todoist
This application, Sync-Notion-Todoist, is designed to provide a two-way synchronization between your Notion database and Todoist tasks. It allows you to manage your tasks seamlessly across both platforms.

# Features
- Fetch tasks from Notion and Todoist.
- Create and delete tasks in Todoist based on your Notion databse tasks.
- Create and delete tasks in Notion database based on your Todoist tasks.
- Update tasks on both Todoist and Notion database
- Automatically sync tasks whenever there are changes in Notion or Todoist.

# Important
Your Notion Database will need to have the following properties or you can modify the code to match your database setup.
|    | Type         | Name |
|----|--------------|------|
| 1. | Title        | Name |
| 2. | Checkbox     | Done |
| 3. | Full Date    | Date |
| 4. | Multi-select | Type |
| 5. | Number       | ID   |

Or you can use my Template here:

https://hugolee001124.notion.site/147e2b7fda31408db8e1149daf7f4406?v=d20f6074f4394947827d341b3b10b64e&pvs=4

# How it Works
The application uses the APIs provided by both Notion and Todoist to fetch and manipulate tasks. It compares the tasks from both platforms and performs necessary updates to keep them in sync.

# Run Locally
1. Clone the repository to your local machine.
2. Install the required Python packages by running `pip install -r requirements.txt`
3. Create a *.env* file in the root directory to include your Notion API tonken, Todoist API tonken and Notion databse ID in the following format:

        NOTION_API_TOKEN = "YOUR_NOTION_API_TOKEN"
	    NOTION_DATABASE_ID = "YOUR_NOTION_DATABASE_ID"
	    TODOIST_API_TOKEN = "YOUR_TODOIST_API_TOKEN"
4. Run `main.py`

# Docker Setup
1. Open the `docker-compose.yml` file.
2. Edit the environment variables: 

        environment:
	       NOTION_API_TOKEN=YOUR_NOTION_API_TOKEN
	       NOTION_DATABASE_ID=YOUR_NOTION_DATABASE_ID
           TODOIST_API_TOKEN=YOUR_TODOIST_API_TOKEN

3. Run `docker-compose up`
