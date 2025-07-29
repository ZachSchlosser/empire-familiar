"""
Google Tasks Operations Module

This module provides functions for creating, reading, updating, and managing Google Tasks.
"""

from googleapiclient.errors import HttpError
from auth import get_authenticated_service
from datetime import datetime, timedelta
import pytz

class TasksManager:
    """Manages Google Tasks operations."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the TasksManager.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        # Get authenticated service specifically for Google Tasks
        from auth import CalendarAuth
        auth = CalendarAuth(credentials_file=credentials_file)
        auth.authenticate()
        
        from googleapiclient.discovery import build
        self.service = build('tasks', 'v1', credentials=auth.creds)
        self.timezone = pytz.timezone('America/New_York')
        print("Google Tasks service initialized")
    
    def get_task_lists(self):
        """
        Get all task lists.
        
        Returns:
            list: List of task lists
        """
        try:
            results = self.service.tasklists().list().execute()
            task_lists = results.get('items', [])
            
            return [{
                'id': tl['id'],
                'title': tl['title'],
                'updated': tl.get('updated', ''),
                'selfLink': tl.get('selfLink', '')
            } for tl in task_lists]
        
        except HttpError as e:
            print(f"HTTP Error getting task lists: {e}")
            return []
        except Exception as e:
            print(f"Error getting task lists: {e}")
            return []
    
    def get_tasks(self, task_list_id='@default', show_completed=False, max_results=50):
        """
        Get tasks from a specific task list.
        
        Args:
            task_list_id (str): Task list ID ('@default' for default list)
            show_completed (bool): Include completed tasks
            max_results (int): Maximum number of tasks to return
        
        Returns:
            list: List of tasks
        """
        try:
            results = self.service.tasks().list(
                tasklist=task_list_id,
                showCompleted=show_completed,
                maxResults=max_results
            ).execute()
            
            tasks = results.get('items', [])
            
            formatted_tasks = []
            for task in tasks:
                formatted_task = {
                    'id': task['id'],
                    'title': task['title'],
                    'status': task.get('status', 'needsAction'),
                    'notes': task.get('notes', ''),
                    'due': task.get('due', None),
                    'completed': task.get('completed', None),
                    'updated': task.get('updated', ''),
                    'parent': task.get('parent', None),
                    'position': task.get('position', ''),
                    'raw': task
                }
                
                # Format due date if present
                if formatted_task['due']:
                    try:
                        due_date = datetime.fromisoformat(formatted_task['due'].replace('Z', '+00:00'))
                        formatted_task['due_formatted'] = due_date.strftime('%Y-%m-%d')
                    except:
                        formatted_task['due_formatted'] = formatted_task['due']
                
                formatted_tasks.append(formatted_task)
            
            return formatted_tasks
        
        except HttpError as e:
            print(f"HTTP Error getting tasks: {e}")
            return []
        except Exception as e:
            print(f"Error getting tasks: {e}")
            return []
    
    def create_task(self, title, notes=None, due_date=None, task_list_id='@default'):
        """
        Create a new task.
        
        Args:
            title (str): Task title
            notes (str): Task notes/description
            due_date (str or datetime): Due date ('YYYY-MM-DD' or datetime object)
            task_list_id (str): Task list ID to add task to
        
        Returns:
            dict: Created task information or None if failed
        """
        try:
            task_body = {
                'title': title
            }
            
            if notes:
                task_body['notes'] = notes
            
            if due_date:
                if isinstance(due_date, str):
                    # Assume YYYY-MM-DD format
                    due_datetime = datetime.strptime(due_date, '%Y-%m-%d')
                elif isinstance(due_date, datetime):
                    due_datetime = due_date
                else:
                    due_datetime = None
                
                if due_datetime:
                    # Google Tasks expects RFC 3339 format
                    task_body['due'] = due_datetime.strftime('%Y-%m-%dT00:00:00.000Z')
            
            created_task = self.service.tasks().insert(
                tasklist=task_list_id,
                body=task_body
            ).execute()
            
            print(f"Task created: '{title}'")
            return {
                'id': created_task['id'],
                'title': created_task['title'],
                'status': created_task.get('status', 'needsAction'),
                'due': created_task.get('due', None),
                'selfLink': created_task.get('selfLink', ''),
                'raw': created_task
            }
        
        except HttpError as e:
            print(f"HTTP Error creating task: {e}")
            return None
        except Exception as e:
            print(f"Error creating task: {e}")
            return None
    
    def update_task(self, task_id, title=None, notes=None, due_date=None, 
                   status=None, task_list_id='@default'):
        """
        Update an existing task.
        
        Args:
            task_id (str): Task ID to update
            title (str): New title
            notes (str): New notes
            due_date (str or datetime): New due date
            status (str): New status ('needsAction' or 'completed')
            task_list_id (str): Task list ID
        
        Returns:
            dict: Updated task information or None if failed
        """
        try:
            # Get the existing task
            existing_task = self.service.tasks().get(
                tasklist=task_list_id,
                task=task_id
            ).execute()
            
            # Update fields if provided
            if title is not None:
                existing_task['title'] = title
            if notes is not None:
                existing_task['notes'] = notes
            if status is not None:
                existing_task['status'] = status
                if status == 'completed':
                    existing_task['completed'] = datetime.now(self.timezone).isoformat()
            
            if due_date is not None:
                if isinstance(due_date, str):
                    due_datetime = datetime.strptime(due_date, '%Y-%m-%d')
                elif isinstance(due_date, datetime):
                    due_datetime = due_date
                else:
                    due_datetime = None
                
                if due_datetime:
                    existing_task['due'] = due_datetime.strftime('%Y-%m-%dT00:00:00.000Z')
            
            # Update the task
            updated_task = self.service.tasks().update(
                tasklist=task_list_id,
                task=task_id,
                body=existing_task
            ).execute()
            
            print(f"Task updated: '{updated_task['title']}'")
            return {
                'id': updated_task['id'],
                'title': updated_task['title'],
                'status': updated_task.get('status', 'needsAction'),
                'due': updated_task.get('due', None),
                'raw': updated_task
            }
        
        except HttpError as e:
            print(f"HTTP Error updating task: {e}")
            return None
        except Exception as e:
            print(f"Error updating task: {e}")
            return None
    
    def complete_task(self, task_id, task_list_id='@default'):
        """
        Mark a task as completed.
        
        Args:
            task_id (str): Task ID to complete
            task_list_id (str): Task list ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_task(task_id, status='completed', task_list_id=task_list_id) is not None
    
    def delete_task(self, task_id, task_list_id='@default'):
        """
        Delete a task.
        
        Args:
            task_id (str): Task ID to delete
            task_list_id (str): Task list ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.service.tasks().delete(
                tasklist=task_list_id,
                task=task_id
            ).execute()
            
            print(f"Task {task_id} deleted successfully")
            return True
        
        except HttpError as e:
            print(f"HTTP Error deleting task: {e}")
            return False
        except Exception as e:
            print(f"Error deleting task: {e}")
            return False
    
    def search_tasks(self, search_query, task_list_id='@default'):
        """
        Search tasks by title or notes.
        
        Args:
            search_query (str): Search query
            task_list_id (str): Task list ID to search in
        
        Returns:
            list: List of matching tasks
        """
        try:
            all_tasks = self.get_tasks(task_list_id=task_list_id, show_completed=True, max_results=100)
            
            search_lower = search_query.lower()
            matching_tasks = []
            
            for task in all_tasks:
                title_match = search_lower in task['title'].lower()
                notes_match = search_lower in task.get('notes', '').lower()
                
                if title_match or notes_match:
                    matching_tasks.append(task)
            
            return matching_tasks
        
        except Exception as e:
            print(f"Error searching tasks: {e}")
            return []
    
    def get_overdue_tasks(self, task_list_id='@default'):
        """
        Get tasks that are overdue.
        
        Args:
            task_list_id (str): Task list ID
        
        Returns:
            list: List of overdue tasks
        """
        try:
            tasks = self.get_tasks(task_list_id=task_list_id, show_completed=False)
            
            today = datetime.now(self.timezone).date()
            overdue_tasks = []
            
            for task in tasks:
                if task['due']:
                    try:
                        due_date = datetime.fromisoformat(task['due'].replace('Z', '+00:00')).date()
                        if due_date < today:
                            overdue_tasks.append(task)
                    except:
                        continue
            
            return overdue_tasks
        
        except Exception as e:
            print(f"Error getting overdue tasks: {e}")
            return []
    
    def get_tasks_due_today(self, task_list_id='@default'):
        """
        Get tasks due today.
        
        Args:
            task_list_id (str): Task list ID
        
        Returns:
            list: List of tasks due today
        """
        try:
            tasks = self.get_tasks(task_list_id=task_list_id, show_completed=False)
            
            today = datetime.now(self.timezone).date()
            today_tasks = []
            
            for task in tasks:
                if task['due']:
                    try:
                        due_date = datetime.fromisoformat(task['due'].replace('Z', '+00:00')).date()
                        if due_date == today:
                            today_tasks.append(task)
                    except:
                        continue
            
            return today_tasks
        
        except Exception as e:
            print(f"Error getting today's tasks: {e}")
            return []
    
    def create_task_from_natural_language(self, description):
        """
        Create a task from natural language description.
        
        Args:
            description (str): Natural language task description
        
        Returns:
            dict: Created task information
        """
        try:
            # Simple parsing for due dates
            import re
            
            # Extract due date patterns
            due_date = None
            title = description
            
            # Look for "due tomorrow", "due today", "due on YYYY-MM-DD", etc.
            if 'due tomorrow' in description.lower():
                due_date = (datetime.now(self.timezone) + timedelta(days=1)).strftime('%Y-%m-%d')
                title = re.sub(r'\s*due tomorrow\s*', ' ', description, flags=re.IGNORECASE).strip()
            elif 'due today' in description.lower():
                due_date = datetime.now(self.timezone).strftime('%Y-%m-%d')
                title = re.sub(r'\s*due today\s*', ' ', description, flags=re.IGNORECASE).strip()
            
            # Look for date patterns like "due on 2025-07-30"
            date_match = re.search(r'due on (\d{4}-\d{2}-\d{2})', description.lower())
            if date_match:
                due_date = date_match.group(1)
                title = re.sub(r'\s*due on \d{4}-\d{2}-\d{2}\s*', ' ', description, flags=re.IGNORECASE).strip()
            
            # Clean up the title
            title = re.sub(r'\s+', ' ', title).strip()
            
            return self.create_task(title, due_date=due_date)
        
        except Exception as e:
            print(f"Error creating task from natural language: {e}")
            return None

def get_tasks_service(credentials_file='credentials.json'):
    """
    Convenience function to get Tasks manager.
    
    Args:
        credentials_file (str): Path to OAuth credentials file
    
    Returns:
        TasksManager: Initialized Tasks manager
    """
    return TasksManager(credentials_file=credentials_file)

if __name__ == "__main__":
    # Test Google Tasks functions
    try:
        tasks = TasksManager()
        
        print("Testing Google Tasks functions...")
        
        # Test getting task lists
        print("\nTask Lists:")
        task_lists = tasks.get_task_lists()
        for tl in task_lists:
            print(f"  • {tl['title']} (ID: {tl['id']})")
        
        # Test getting tasks from default list
        print("\nTasks in default list:")
        all_tasks = tasks.get_tasks(show_completed=False, max_results=10)
        for task in all_tasks:
            due_info = f" (due: {task.get('due_formatted', 'No due date')})" if task.get('due') else ""
            print(f"  • {task['title']}{due_info}")
        
        print(f"\nGoogle Tasks service ready! Found {len(all_tasks)} active tasks.")
        
    except Exception as e:
        print(f"Error testing Google Tasks functions: {e}")
        print("Make sure you've completed re-authentication with Google Tasks scopes.")