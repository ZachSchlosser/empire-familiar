"""
Integrated Google Assistant - Calendar, Gmail, and Google Docs

This is the unified interface that Claude Code can use to manage calendar,
email, and documents using natural language commands.
"""

from main import CalendarScheduler
from gmail_functions import GmailManager
from docs_functions import DocsManager
from tasks_functions import TasksManager
import re

class IntegratedGoogleAssistant:
    """Natural language interface for Google Calendar, Gmail, Docs, and Tasks."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the IntegratedGoogleAssistant.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        print("Initializing integrated Google services...")
        
        self.calendar = CalendarScheduler(credentials_file)
        self.gmail = GmailManager(credentials_file)
        self.docs = DocsManager(credentials_file)
        self.tasks = TasksManager(credentials_file)
        
        print("🎉 Integrated Google Assistant ready!")
        print("Available services: Calendar 📅, Gmail 📧, Google Docs 📄, Tasks ✅")
    
    # CALENDAR FUNCTIONS
    def schedule_event(self, description):
        """Schedule a calendar event using natural language."""
        return self.calendar.schedule_event(description)
    
    def get_schedule(self, time_period="today"):
        """Get calendar schedule for specified time period."""
        return self.calendar.get_schedule(time_period)
    
    def find_free_time(self, duration="1 hour", when="this week"):
        """Find available time slots in calendar."""
        return self.calendar.find_available_time(duration, when)
    
    def cancel_event(self, event_identifier):
        """Cancel a calendar event."""
        return self.calendar.cancel_event(event_identifier)
    
    def reschedule_event(self, event_identifier, new_time):
        """Reschedule a calendar event."""
        return self.calendar.reschedule_event(event_identifier, new_time)
    
    # GMAIL FUNCTIONS
    def get_unread_emails(self, max_count=10):
        """Get unread Gmail messages."""
        return self.gmail.get_unread_messages(max_count)
    
    def send_email(self, to_email, subject, body):
        """Send an email."""
        return self.gmail.send_email(to_email, subject, body)
    
    def reply_to_email(self, message_id, reply_text):
        """Reply to a specific email."""
        return self.gmail.reply_to_message(message_id, reply_text)
    
    def search_emails(self, search_query, max_results=10):
        """Search emails with natural language."""
        return self.gmail.search_messages(search_query, max_results)
    
    def mark_email_read(self, message_id):
        """Mark an email as read."""
        return self.gmail.mark_as_read(message_id)
    
    # GOOGLE DOCS FUNCTIONS
    def create_document(self, title, content=None):
        """Create a new Google Doc."""
        return self.docs.create_document(title, content)
    
    def read_document(self, document_id):
        """Read content from a Google Doc."""
        return self.docs.read_document(document_id)
    
    def add_to_document(self, document_id, text):
        """Add text to a Google Doc."""
        return self.docs.append_to_document(document_id, text)
    
    def get_recent_documents(self, max_count=10):
        """Get list of recent Google Docs."""
        return self.docs.list_recent_documents(max_count)
    
    def share_document(self, document_id, email, role='writer'):
        """Share a document with someone."""
        return self.docs.share_document(document_id, email, role)
    
    # GOOGLE TASKS FUNCTIONS
    def get_task_lists(self):
        """Get all task lists."""
        return self.tasks.get_task_lists()
    
    def get_tasks(self, task_list_id='@default', show_completed=False):
        """Get tasks from specified task list."""
        return self.tasks.get_tasks(task_list_id, show_completed)
    
    def create_task(self, title, notes=None, due_date=None):
        """Create a new task."""
        return self.tasks.create_task(title, notes, due_date)
    
    def create_task_from_description(self, description):
        """Create a task from natural language description."""
        return self.tasks.create_task_from_natural_language(description)
    
    def complete_task(self, task_id):
        """Mark a task as completed."""
        return self.tasks.complete_task(task_id)
    
    def update_task(self, task_id, title=None, notes=None, due_date=None, status=None):
        """Update an existing task."""
        return self.tasks.update_task(task_id, title, notes, due_date, status)
    
    def delete_task(self, task_id):
        """Delete a task."""
        return self.tasks.delete_task(task_id)
    
    def search_tasks(self, search_query):
        """Search tasks by title or notes."""
        return self.tasks.search_tasks(search_query)
    
    def get_overdue_tasks(self):
        """Get tasks that are overdue."""
        return self.tasks.get_overdue_tasks()
    
    def get_tasks_due_today(self):
        """Get tasks due today."""
        return self.tasks.get_tasks_due_today()
    
    # INTEGRATED WORKFLOWS
    def create_meeting_with_agenda(self, meeting_description, agenda_items):
        """
        Create a calendar event and a Google Doc agenda.
        
        Args:
            meeting_description (str): Natural language meeting description
            agenda_items (list): List of agenda items
        
        Returns:
            dict: Information about created event and document
        """
        print(f"Creating meeting with agenda: {meeting_description}")
        
        # Schedule the meeting
        event = self.schedule_event(meeting_description)
        if not event:
            return {"error": "Failed to create calendar event"}
        
        # Extract meeting title for document
        meeting_title = event.get('summary', 'Meeting')
        
        # Create agenda document
        agenda_content = f"{meeting_title} - Agenda\n\n"
        agenda_content += f"Date: {event.get('start', {}).get('dateTime', 'TBD')}\n\n"
        agenda_content += "Agenda Items:\n"
        
        for i, item in enumerate(agenda_items, 1):
            agenda_content += f"{i}. {item}\n"
        
        agenda_content += "\n\nNotes:\n\n\n\nAction Items:\n\n"
        
        doc = self.create_document(f"{meeting_title} - Agenda", agenda_content)
        
        return {
            "event": event,
            "agenda_doc": doc,
            "meeting_title": meeting_title
        }
    
    def email_meeting_details(self, event_details, attendee_emails, agenda_doc_url=None):
        """
        Email meeting details to attendees.
        
        Args:
            event_details (dict): Calendar event details
            attendee_emails (list): List of attendee email addresses
            agenda_doc_url (str): URL to agenda document (optional)
        
        Returns:
            list: Results of email sending attempts
        """
        meeting_title = event_details.get('summary', 'Meeting')
        start_time = event_details.get('start', {}).get('dateTime', 'TBD')
        
        subject = f"Meeting Invitation: {meeting_title}"
        
        body = f"Hi,\n\n"
        body += f"You're invited to: {meeting_title}\n"
        body += f"Time: {start_time}\n\n"
        
        if agenda_doc_url:
            body += f"Agenda: {agenda_doc_url}\n\n"
        
        body += "Looking forward to seeing you there!\n\n"
        body += "Best regards"
        
        results = []
        for email in attendee_emails:
            result = self.send_email(email, subject, body)
            results.append({
                "email": email,
                "success": result is not None,
                "result": result
            })
        
        return results
    
    def process_natural_request(self, request):
        """
        Process a natural language request and route to appropriate service.
        
        Args:
            request (str): Natural language request
        
        Returns:
            dict: Result of the processed request
        """
        request_lower = request.lower()
        
        # Calendar-related requests
        if any(word in request_lower for word in ['schedule', 'meeting', 'appointment', 'calendar', 'book']):
            if 'cancel' in request_lower:
                # Extract event name to cancel
                event_name = self._extract_event_name_for_cancel(request)
                return {"action": "cancel_event", "result": self.cancel_event(event_name)}
            else:
                return {"action": "schedule_event", "result": self.schedule_event(request)}
        
        # Email-related requests
        elif any(word in request_lower for word in ['email', 'mail', 'send', 'unread']):
            if 'unread' in request_lower:
                return {"action": "get_unread", "result": self.get_unread_emails()}
            elif 'send' in request_lower:
                # This would need more parsing for full automation
                return {"action": "send_email", "message": "Please provide recipient, subject, and body"}
        
        # Document-related requests
        elif any(word in request_lower for word in ['document', 'doc', 'create', 'write']):
            if 'create' in request_lower:
                # Extract title from request
                title = self._extract_document_title(request)
                return {"action": "create_document", "result": self.create_document(title)}
        
        # Default: return guidance
        return {
            "action": "unknown",
            "message": "I can help with calendar scheduling, email management, and document creation. Please be more specific."
        }
    
    def _extract_event_name_for_cancel(self, request):
        """Extract event name from cancellation request."""
        # Simple extraction - could be improved
        patterns = [
            r'cancel\s+(?:the\s+)?(.+?)(?:\s+event|\s+meeting|$)',
            r'cancel\s+(.+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "meeting"  # default
    
    def _extract_document_title(self, request):
        """Extract document title from creation request."""
        patterns = [
            r'create\s+(?:a\s+)?document\s+(?:called\s+)?["\'](.+?)["\']',
            r'create\s+(?:a\s+)?document\s+(?:called\s+)?(.+?)(?:\s+with|\s+about|$)',
            r'create\s+(.+?)\s+document'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, request, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "New Document"  # default

def main():
    """Main function for testing the integrated assistant."""
    try:
        assistant = IntegratedGoogleAssistant()
        
        print("\n🚀 Google Assistant is ready!")
        print("\nExample commands:")
        print("- assistant.schedule_event('Schedule team meeting tomorrow at 2 PM')")
        print("- assistant.get_unread_emails()")
        print("- assistant.create_document('Meeting Notes', 'Initial content here')")
        print("- assistant.get_schedule('today')")
        print("- assistant.create_task('Finish project report', due_date='2025-07-30')")
        print("- assistant.get_tasks_due_today()")
        print("- assistant.get_overdue_tasks()")
        
        return assistant
        
    except Exception as e:
        print(f"Error initializing assistant: {e}")
        return None

if __name__ == "__main__":
    main()