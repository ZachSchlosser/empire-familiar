"""
Google Calendar OAuth Authentication Module

This module handles OAuth 2.0 authentication for Google Calendar API.
"""

import os
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# Define the scopes for Google Calendar, Gmail, Google Docs, and Google Tasks APIs
SCOPES = [
    'https://www.googleapis.com/auth/calendar',           # Google Calendar access
    'https://www.googleapis.com/auth/gmail.readonly',     # Read Gmail messages
    'https://www.googleapis.com/auth/gmail.send',         # Send Gmail messages
    'https://www.googleapis.com/auth/gmail.modify',       # Modify Gmail (labels, etc.)
    'https://www.googleapis.com/auth/documents',          # Google Docs read/write
    'https://www.googleapis.com/auth/drive.file',         # Access Google Drive files
    'https://www.googleapis.com/auth/tasks'               # Google Tasks read/write
]

class CalendarAuth:
    """Handles Google Calendar authentication and service creation."""
    
    def __init__(self, credentials_file='credentials.json', token_file='token.json'):
        """
        Initialize the CalendarAuth object.
        
        Args:
            credentials_file (str): Path to the OAuth credentials JSON file
            token_file (str): Path to store the access token
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.creds = None
        self.service = None
    
    def authenticate(self):
        """
        Authenticate with Google Calendar API using OAuth 2.0.
        
        Returns:
            google.oauth2.credentials.Credentials: The authenticated credentials
        """
        # Load existing token if available
        if os.path.exists(self.token_file):
            with open(self.token_file, 'rb') as token:
                self.creds = pickle.load(token)
        
        # If there are no valid credentials available, request authorization
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                # Refresh the token
                try:
                    self.creds.refresh(Request())
                    print("Token refreshed successfully")
                except Exception as e:
                    print(f"Token refresh failed: {e}")
                    self.creds = None
            
            if not self.creds:
                # Run the OAuth flow
                if not os.path.exists(self.credentials_file):
                    raise FileNotFoundError(
                        f"Credentials file '{self.credentials_file}' not found. "
                        "Please download your OAuth credentials from Google Cloud Console."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, 
                    SCOPES
                )
                self.creds = flow.run_local_server(port=0)
                print("New authentication completed")
            
            # Save the credentials for the next run
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.creds, token)
                print(f"Token saved to {self.token_file}")
        
        return self.creds
    
    def get_calendar_service(self):
        """
        Get the Google Calendar service object.
        
        Returns:
            googleapiclient.discovery.Resource: The Calendar service object
        """
        if not self.creds:
            self.authenticate()
        
        if not self.service:
            self.service = build('calendar', 'v3', credentials=self.creds)
            print("Calendar service initialized")
        
        return self.service
    
    def is_authenticated(self):
        """
        Check if the user is currently authenticated.
        
        Returns:
            bool: True if authenticated, False otherwise
        """
        return self.creds is not None and self.creds.valid

def get_authenticated_service(credentials_file='credentials.json'):
    """
    Convenience function to get an authenticated Calendar service.
    
    Args:
        credentials_file (str): Path to the OAuth credentials JSON file
    
    Returns:
        googleapiclient.discovery.Resource: The authenticated Calendar service
    """
    auth = CalendarAuth(credentials_file=credentials_file)
    return auth.get_calendar_service()

if __name__ == "__main__":
    # Test authentication
    try:
        service = get_authenticated_service()
        print("Authentication successful!")
        
        # Test by getting calendar list
        calendars_result = service.calendarList().list().execute()
        calendars = calendars_result.get('items', [])
        
        print(f"\nFound {len(calendars)} calendar(s):")
        for calendar in calendars:
            print(f"  - {calendar['summary']} ({calendar['id']})")
            
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nTo set up authentication:")
        print("1. Go to Google Cloud Console")
        print("2. Create a new project or select existing one")
        print("3. Enable Google Calendar API")
        print("4. Create OAuth 2.0 credentials")
        print("5. Download the credentials.json file to this directory")
    except Exception as e:
        print(f"Authentication failed: {e}")