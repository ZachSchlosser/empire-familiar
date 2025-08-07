"""
Gmail Operations Module

This module provides functions for reading, sending, and managing Gmail messages.
"""

import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from googleapiclient.errors import HttpError
from auth import get_authenticated_service

class GmailManager:
    """Manages Gmail operations."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the GmailManager.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        # Get authenticated service specifically for Gmail
        from auth import CalendarAuth
        auth = CalendarAuth(credentials_file=credentials_file)
        auth.authenticate()
        
        from googleapiclient.discovery import build
        self.service = build('gmail', 'v1', credentials=auth.creds)
        print("Gmail service initialized")
    
    def get_messages(self, query='', max_results=10):
        """
        Get Gmail messages based on query.
        
        Args:
            query (str): Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')
            max_results (int): Maximum number of messages to return
        
        Returns:
            list: List of message objects
        """
        try:
            # Get message IDs
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            
            # Get full message details
            detailed_messages = []
            for message in messages:
                msg = self.service.users().messages().get(
                    userId='me',
                    id=message['id']
                ).execute()
                detailed_messages.append(msg)
            
            return detailed_messages
        
        except HttpError as e:
            print(f"HTTP Error getting messages: {e}")
            return []
        except Exception as e:
            print(f"Error getting messages: {e}")
            return []
    
    def get_unread_messages(self, max_results=10):
        """
        Get unread Gmail messages.
        
        Args:
            max_results (int): Maximum number of messages to return
        
        Returns:
            list: List of unread messages with formatted details
        """
        messages = self.get_messages(query='is:unread', max_results=max_results)
        
        formatted_messages = []
        for msg in messages:
            formatted_msg = self.format_message(msg)
            if formatted_msg:
                formatted_messages.append(formatted_msg)
        
        return formatted_messages
    
    def send_email(self, to_email, subject, body, html_body=None, threading_headers=None, thread_id=None):
        """
        Send an email with optional threading headers for conversation threading.
        
        Args:
            to_email (str): Recipient email address
            subject (str): Email subject
            body (str): Plain text body
            html_body (str): HTML body (optional)
            threading_headers (dict): Threading headers with keys:
                - message_id (str): Message-ID for this email
                - in_reply_to (str): In-Reply-To header for replies
                - references (str): References header for full thread chain
            thread_id (str): Gmail thread ID to reply to (optional)
        
        Returns:
            dict: Sent message information with message_id or None if failed
        """
        try:
            # Create message
            if html_body:
                message = MIMEMultipart('alternative')
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(html_body, 'html')
                message.attach(text_part)
                message.attach(html_part)
            else:
                message = MIMEText(body)
            
            message['to'] = to_email
            message['subject'] = subject
            
            # Set From field to authenticated email
            try:
                profile = self.service.users().getProfile(userId='me').execute()
                authenticated_email = profile["emailAddress"]
                message['from'] = authenticated_email
            except:
                pass  # Let Gmail use default if profile fetch fails
            
            # Add threading headers for email conversation threading
            if threading_headers:
                if 'message_id' in threading_headers and threading_headers['message_id']:
                    message['Message-ID'] = threading_headers['message_id']
                
                if 'in_reply_to' in threading_headers and threading_headers['in_reply_to']:
                    message['In-Reply-To'] = threading_headers['in_reply_to']
                
                if 'references' in threading_headers and threading_headers['references']:
                    message['References'] = threading_headers['references']
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            # Prepare message body
            message_body = {'raw': raw_message}
            
            # CRITICAL: Add threadId if replying to existing thread
            if thread_id:
                message_body['threadId'] = thread_id
                print(f"  🔗 THREAD CONTINUITY: Replying to existing thread")
                print(f"     Thread ID: {thread_id}")
                print(f"     Subject: {subject}")
            else:
                print(f"  🆕 NEW THREAD: No thread ID provided")
                print(f"     Subject: {subject}")
            
            # Log the exact request body for debugging
            print(f"  📤 Gmail API Request: threadId={'✓' if 'threadId' in message_body else '✗'}")
            
            # Send message
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message_body
            ).execute()
            
            # Add the message_id to the response for threading purposes
            if sent_message and threading_headers and 'message_id' in threading_headers:
                sent_message['custom_message_id'] = threading_headers['message_id']
            
            # Log thread verification
            response_thread_id = sent_message.get('threadId') if sent_message else None
            if response_thread_id:
                if thread_id and response_thread_id == thread_id:
                    print(f"  ✅ THREAD VERIFIED: Gmail confirmed same thread")
                elif thread_id and response_thread_id != thread_id:
                    print(f"  ⚠️  THREAD MISMATCH: Expected {thread_id}, got {response_thread_id}")
                else:
                    print(f"  🆕 NEW THREAD CREATED: {response_thread_id}")
            
            print(f"Email sent successfully to {to_email}")
            if threading_headers:
                print(f"  Threading headers: Message-ID={threading_headers.get('message_id', 'None')}")
                print(f"  In-Reply-To={threading_headers.get('in_reply_to', 'None')}")
            
            return sent_message
        
        except HttpError as e:
            print(f"HTTP Error sending email: {e}")
            return None
        except Exception as e:
            print(f"Error sending email: {e}")
            return None
    
    def archive_thread(self, thread_id):
        """
        Archive an entire email thread by removing INBOX label from all messages in the thread.
        
        Args:
            thread_id (str): Gmail thread ID to archive
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get all messages in the thread
            thread = self.service.users().threads().get(
                userId='me',
                id=thread_id
            ).execute()
            
            messages = thread.get('messages', [])
            if not messages:
                print(f"No messages found in thread {thread_id}")
                return False
            
            # Archive each message in the thread by removing INBOX label
            archived_count = 0
            for message in messages:
                message_id = message['id']
                
                # Check if message has INBOX label
                current_labels = message.get('labelIds', [])
                if 'INBOX' in current_labels:
                    # Remove INBOX label to archive the message
                    modify_request = {
                        'removeLabelIds': ['INBOX']
                    }
                    
                    self.service.users().messages().modify(
                        userId='me',
                        id=message_id,
                        body=modify_request
                    ).execute()
                    
                    archived_count += 1
            
            print(f"✅ Archived thread {thread_id} ({archived_count} messages)")
            return True
            
        except HttpError as e:
            print(f"HTTP Error archiving thread {thread_id}: {e}")
            return False
        except Exception as e:
            print(f"Error archiving thread {thread_id}: {e}")
            return False
    
    def reply_to_message(self, message_id, reply_body):
        """
        Reply to a specific message with proper Gmail threading.
        
        Args:
            message_id (str): ID of message to reply to
            reply_body (str): Reply content
        
        Returns:
            dict: Reply message information or None if failed
        """
        try:
            # Get original message
            original_msg = self.service.users().messages().get(
                userId='me',
                id=message_id
            ).execute()
            
            # Extract headers
            headers = original_msg['payload'].get('headers', [])
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), '')
            to_email = next((h['value'] for h in headers if h['name'].lower() == 'to'), '')
            original_message_id = next((h['value'] for h in headers if h['name'].lower() == 'message-id'), '')
            references = next((h['value'] for h in headers if h['name'].lower() == 'references'), '')
            
            # Create reply subject
            reply_subject = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            # Build proper threading headers for Gmail reply chain
            threading_headers = {}
            
            # Set In-Reply-To to the original message's Message-ID
            if original_message_id:
                threading_headers['in_reply_to'] = original_message_id
                
                # Build References header chain
                if references:
                    # Append original message ID to existing references
                    threading_headers['references'] = f"{references} {original_message_id}"
                else:
                    # Start references chain with original message ID
                    threading_headers['references'] = original_message_id
            
            # Send reply with proper threading headers
            return self.send_email(
                to_email=from_email,
                subject=reply_subject,
                body=reply_body,
                threading_headers=threading_headers
            )
        
        except Exception as e:
            print(f"Error replying to message: {e}")
            return None
    
    def format_message(self, message):
        """
        Format a Gmail message for display.
        
        Args:
            message (dict): Gmail message object
        
        Returns:
            dict: Formatted message information
        """
        try:
            headers = message['payload'].get('headers', [])
            
            # Extract key information
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            from_email = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown Sender')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), 'Unknown Date')
            
            # Extract body
            body = self.extract_message_body(message['payload'])
            
            return {
                'id': message['id'],
                'subject': subject,
                'from': from_email,
                'date': date,
                'body': body[:500],  # First 500 characters
                'full_body': body,
                'thread_id': message.get('threadId', ''),
                'labels': message.get('labelIds', [])
            }
        
        except Exception as e:
            print(f"Error formatting message: {e}")
            return None
    
    def extract_message_body(self, payload):
        """
        Extract body text from message payload.
        
        Args:
            payload (dict): Message payload
        
        Returns:
            str: Extracted body text
        """
        body = ""
        
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
                elif part['mimeType'] == 'text/html' and not body:
                    data = part['body']['data']
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['mimeType'] == 'text/plain':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        elif payload['mimeType'] == 'text/html':
            data = payload['body']['data']
            body = base64.urlsafe_b64decode(data).decode('utf-8')
        
        return body
    
    def mark_as_read(self, message_id):
        """
        Mark a message as read.
        
        Args:
            message_id (str): ID of message to mark as read
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            
            print(f"Message {message_id} marked as read")
            return True
        
        except Exception as e:
            print(f"Error marking message as read: {e}")
            return False
    
    def search_messages(self, search_query, max_results=10):
        """
        Search Gmail messages with natural language query.
        
        Args:
            search_query (str): Search query
            max_results (int): Maximum results to return
        
        Returns:
            list: List of matching messages
        """
        # Convert natural language to Gmail query
        gmail_query = self.convert_to_gmail_query(search_query)
        return self.get_messages(query=gmail_query, max_results=max_results)
    
    def convert_to_gmail_query(self, natural_query):
        """
        Convert natural language to Gmail search query.
        
        Args:
            natural_query (str): Natural language search
        
        Returns:
            str: Gmail search query
        """
        query_lower = natural_query.lower()
        
        # Common conversions
        if 'unread' in query_lower:
            return 'is:unread'
        elif 'from' in query_lower and '@' in natural_query:
            # Extract email from natural language
            import re
            email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', natural_query)
            if email_match:
                return f'from:{email_match.group()}'
        elif 'today' in query_lower:
            return 'newer_than:1d'
        elif 'this week' in query_lower:
            return 'newer_than:7d'
        
        # Default: return as-is
        return natural_query

def get_gmail_service(credentials_file='credentials.json'):
    """
    Convenience function to get Gmail manager.
    
    Args:
        credentials_file (str): Path to OAuth credentials file
    
    Returns:
        GmailManager: Initialized Gmail manager
    """
    return GmailManager(credentials_file=credentials_file)

if __name__ == "__main__":
    # Test Gmail functions
    try:
        gmail = GmailManager()
        
        print("Testing Gmail functions...")
        
        # Test getting unread messages
        print("\nUnread messages:")
        unread = gmail.get_unread_messages(max_results=3)
        for msg in unread:
            print(f"  • {msg['subject']} from {msg['from']}")
        
        print(f"\nGmail service ready! Found {len(unread)} unread messages.")
        
    except Exception as e:
        print(f"Error testing Gmail functions: {e}")
        print("Make sure you've completed re-authentication with Gmail scopes.")