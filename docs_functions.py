"""
Google Docs Operations Module

This module provides functions for creating, reading, and editing Google Docs.
"""

from googleapiclient.errors import HttpError
from auth import get_authenticated_service

class DocsManager:
    """Manages Google Docs operations."""
    
    def __init__(self, credentials_file='credentials.json'):
        """
        Initialize the DocsManager.
        
        Args:
            credentials_file (str): Path to OAuth credentials file
        """
        # Get authenticated service specifically for Google Docs
        from auth import CalendarAuth
        auth = CalendarAuth(credentials_file=credentials_file)
        auth.authenticate()
        
        from googleapiclient.discovery import build
        self.docs_service = build('docs', 'v1', credentials=auth.creds)
        self.drive_service = build('drive', 'v3', credentials=auth.creds)
        print("Google Docs service initialized")
    
    def create_document(self, title, content=None):
        """
        Create a new Google Doc.
        
        Args:
            title (str): Document title
            content (str): Initial content (optional)
        
        Returns:
            dict: Created document information
        """
        try:
            # Create the document
            doc = self.docs_service.documents().create(
                body={'title': title}
            ).execute()
            
            document_id = doc.get('documentId')
            
            # Add content if provided
            if content:
                self.add_text_to_document(document_id, content)
            
            print(f"Document '{title}' created with ID: {document_id}")
            
            # Get shareable link
            doc_url = f"https://docs.google.com/document/d/{document_id}/edit"
            
            return {
                'id': document_id,
                'title': title,
                'url': doc_url,
                'raw': doc
            }
        
        except HttpError as e:
            print(f"HTTP Error creating document: {e}")
            return None
        except Exception as e:
            print(f"Error creating document: {e}")
            return None
    
    def read_document(self, document_id):
        """
        Read content from a Google Doc.
        
        Args:
            document_id (str): Document ID
        
        Returns:
            dict: Document content and metadata
        """
        try:
            # Get the document
            doc = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            # Extract text content
            content = self.extract_text_from_doc(doc)
            
            return {
                'id': document_id,
                'title': doc.get('title', 'Untitled'),
                'content': content,
                'url': f"https://docs.google.com/document/d/{document_id}/edit",
                'raw': doc
            }
        
        except HttpError as e:
            print(f"HTTP Error reading document: {e}")
            return None
        except Exception as e:
            print(f"Error reading document: {e}")
            return None
    
    def add_text_to_document(self, document_id, text, index=1):
        """
        Add text to a Google Doc.
        
        Args:
            document_id (str): Document ID
            text (str): Text to add
            index (int): Position to insert text (1 = beginning)
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            requests = [
                {
                    'insertText': {
                        'location': {'index': index},
                        'text': text
                    }
                }
            ]
            
            self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            print(f"Text added to document {document_id}")
            return True
        
        except HttpError as e:
            print(f"HTTP Error adding text: {e}")
            return False
        except Exception as e:
            print(f"Error adding text: {e}")
            return False
    
    def replace_text_in_document(self, document_id, find_text, replace_text):
        """
        Replace text in a Google Doc.
        
        Args:
            document_id (str): Document ID
            find_text (str): Text to find
            replace_text (str): Text to replace with
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            requests = [
                {
                    'replaceAllText': {
                        'containsText': {
                            'text': find_text,
                            'matchCase': False
                        },
                        'replaceText': replace_text
                    }
                }
            ]
            
            result = self.docs_service.documents().batchUpdate(
                documentId=document_id,
                body={'requests': requests}
            ).execute()
            
            replacements = result.get('replies', [{}])[0].get('replaceAllText', {}).get('occurrencesChanged', 0)
            print(f"Replaced {replacements} occurrences of '{find_text}' with '{replace_text}'")
            
            return True
        
        except HttpError as e:
            print(f"HTTP Error replacing text: {e}")
            return False
        except Exception as e:
            print(f"Error replacing text: {e}")
            return False
    
    def extract_text_from_doc(self, doc):
        """
        Extract plain text from a Google Doc object.
        
        Args:
            doc (dict): Google Doc object
        
        Returns:
            str: Extracted text content
        """
        content = doc.get('body', {}).get('content', [])
        text = ""
        
        for element in content:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_element in paragraph.get('elements', []):
                    text_run = text_element.get('textRun', {})
                    text += text_run.get('content', '')
        
        return text.strip()
    
    def list_recent_documents(self, max_results=10):
        """
        List recent Google Docs documents.
        
        Args:
            max_results (int): Maximum number of documents to return
        
        Returns:
            list: List of recent documents
        """
        try:
            # Query for Google Docs files
            results = self.drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document'",
                orderBy='modifiedTime desc',
                pageSize=max_results,
                fields="files(id, name, modifiedTime, webViewLink)"
            ).execute()
            
            files = results.get('files', [])
            
            documents = []
            for file in files:
                documents.append({
                    'id': file['id'],
                    'title': file['name'],
                    'modified': file.get('modifiedTime', 'Unknown'),
                    'url': file.get('webViewLink', '')
                })
            
            return documents
        
        except HttpError as e:
            print(f"HTTP Error listing documents: {e}")
            return []
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []
    
    def share_document(self, document_id, email, role='writer'):
        """
        Share a document with someone.
        
        Args:
            document_id (str): Document ID
            email (str): Email address to share with
            role (str): Permission level ('reader', 'writer', 'owner')
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            permission = {
                'type': 'user',
                'role': role,
                'emailAddress': email
            }
            
            self.drive_service.permissions().create(
                fileId=document_id,
                body=permission,
                sendNotificationEmail=True
            ).execute()
            
            print(f"Document shared with {email} as {role}")
            return True
        
        except HttpError as e:
            print(f"HTTP Error sharing document: {e}")
            return False
        except Exception as e:
            print(f"Error sharing document: {e}")
            return False
    
    def create_document_from_template(self, template_text, replacements):
        """
        Create a document from a template with replacements.
        
        Args:
            template_text (str): Template text with placeholders like {{name}}
            replacements (dict): Dictionary of replacements {'name': 'John'}
        
        Returns:
            dict: Created document information
        """
        try:
            # Replace placeholders
            content = template_text
            for placeholder, value in replacements.items():
                content = content.replace(f"{{{{{placeholder}}}}}", str(value))
            
            # Generate title from first line or use placeholder
            title = content.split('\n')[0][:50] if content else "Document from Template"
            
            # Create document
            return self.create_document(title=title, content=content)
        
        except Exception as e:
            print(f"Error creating document from template: {e}")
            return None
    
    def append_to_document(self, document_id, text):
        """
        Append text to the end of a Google Doc.
        
        Args:
            document_id (str): Document ID
            text (str): Text to append
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current document to find the end
            doc = self.docs_service.documents().get(
                documentId=document_id
            ).execute()
            
            # Find the end index
            content = doc.get('body', {}).get('content', [])
            end_index = 1
            
            for element in content:
                if 'endIndex' in element:
                    end_index = max(end_index, element['endIndex'])
            
            # Append text at the end
            return self.add_text_to_document(document_id, f"\n{text}", end_index - 1)
        
        except HttpError as e:
            print(f"HTTP Error appending text: {e}")
            return False
        except Exception as e:
            print(f"Error appending text: {e}")
            return False

def get_docs_service(credentials_file='credentials.json'):
    """
    Convenience function to get Docs manager.
    
    Args:
        credentials_file (str): Path to OAuth credentials file
    
    Returns:
        DocsManager: Initialized Docs manager
    """
    return DocsManager(credentials_file=credentials_file)

if __name__ == "__main__":
    # Test Google Docs functions
    try:
        docs = DocsManager()
        
        print("Testing Google Docs functions...")
        
        # Test listing recent documents
        print("\nRecent documents:")
        recent_docs = docs.list_recent_documents(max_results=3)
        for doc in recent_docs:
            print(f"  • {doc['title']} (ID: {doc['id'][:20]}...)")
        
        print(f"\nGoogle Docs service ready! Found {len(recent_docs)} recent documents.")
        
    except Exception as e:
        print(f"Error testing Google Docs functions: {e}")
        print("Make sure you've completed re-authentication with Google Docs scopes.")