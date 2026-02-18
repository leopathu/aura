"""
Gmail Service
Handles Gmail API interactions using OAuth tokens
"""

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import base64
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.oauth_service import get_decrypted_access_token, get_oauth_token


# Gmail OAuth scopes
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.modify'
]


class GmailClient:
    """Gmail API client wrapper"""
    
    def __init__(self, access_token: str):
        """
        Initialize Gmail client with access token
        
        Args:
            access_token: OAuth access token
        """
        credentials = Credentials(token=access_token)
        self.service = build('gmail', 'v1', credentials=credentials)
    
    def list_messages(
        self,
        max_results: int = 10,
        query: Optional[str] = None,
        label_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        List Gmail messages
        
        Args:
            max_results: Maximum number of messages to return
            query: Gmail search query (e.g., "from:user@example.com")
            label_ids: List of label IDs to filter by
            
        Returns:
            List of message dictionaries
        """
        try:
            params = {
                'userId': 'me',
                'maxResults': max_results
            }
            
            if query:
                params['q'] = query
            
            if label_ids:
                params['labelIds'] = label_ids
            
            results = self.service.users().messages().list(**params).execute()
            messages = results.get('messages', [])
            
            # Get full message details
            detailed_messages = []
            for msg in messages:
                detailed_msg = self.get_message(msg['id'])
                if detailed_msg:
                    detailed_messages.append(detailed_msg)
            
            return detailed_messages
        
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
    
    def get_message(self, message_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a single Gmail message by ID
        
        Args:
            message_id: Message ID
            
        Returns:
            Message dictionary or None
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()
            
            # Parse message details
            headers = message.get('payload', {}).get('headers', [])
            
            # Extract common headers
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), '')
            from_email = next((h['value'] for h in headers if h['name'] == 'From'), '')
            to_email = next((h['value'] for h in headers if h['name'] == 'To'), '')
            date = next((h['value'] for h in headers if h['name'] == 'Date'), '')
            
            # Extract body
            body = self._extract_message_body(message.get('payload', {}))
            
            return {
                'id': message['id'],
                'thread_id': message.get('threadId'),
                'subject': subject,
                'from': from_email,
                'to': to_email,
                'date': date,
                'snippet': message.get('snippet', ''),
                'body': body,
                'labels': message.get('labelIds', [])
            }
        
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
    
    def _extract_message_body(self, payload: Dict[str, Any]) -> str:
        """
        Extract message body from payload
        
        Args:
            payload: Message payload
            
        Returns:
            Message body text
        """
        if 'parts' in payload:
            # Multipart message
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
                elif part['mimeType'] == 'text/html':
                    # Fallback to HTML if no plain text
                    data = part.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
        else:
            # Single part message
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8')
        
        return ''
    
    def send_message(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an email message
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body (plain text)
            from_email: Optional sender email (defaults to authenticated user)
            
        Returns:
            Sent message details
        """
        try:
            # Create message
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            if from_email:
                message['from'] = from_email
            
            # Encode message
            encoded_message = base64.urlsafe_b64encode(
                message.as_bytes()
            ).decode()
            
            # Send message
            send_result = self.service.users().messages().send(
                userId='me',
                body={'raw': encoded_message}
            ).execute()
            
            return {
                'id': send_result['id'],
                'thread_id': send_result.get('threadId'),
                'label_ids': send_result.get('labelIds', [])
            }
        
        except HttpError as error:
            raise Exception(f"Gmail API error: {error}")
    
    def search_messages(
        self,
        query: str,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search Gmail messages
        
        Args:
            query: Gmail search query
            max_results: Maximum number of results
            
        Returns:
            List of matching messages
        """
        return self.list_messages(max_results=max_results, query=query)


async def get_gmail_client(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> Optional[GmailClient]:
    """
    Get Gmail client for user
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        Gmail client or None
    """
    # Get OAuth token
    oauth_token = await get_oauth_token(db, user_id, org_id, 'google')
    if not oauth_token:
        return None
    
    # Get decrypted access token
    access_token = await get_decrypted_access_token(db, user_id, org_id, 'google')
    if not access_token:
        return None
    
    return GmailClient(access_token)


# Convenience functions for direct use

async def list_emails(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    max_results: int = 10,
    query: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List emails for user
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        max_results: Maximum number of emails
        query: Optional search query
        
    Returns:
        List of emails
    """
    client = await get_gmail_client(db, user_id, org_id)
    if not client:
        raise Exception("Gmail not connected")
    
    return client.list_messages(max_results=max_results, query=query)


async def read_email(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    message_id: str
) -> Optional[Dict[str, Any]]:
    """
    Read a specific email
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        message_id: Message ID
        
    Returns:
        Email details or None
    """
    client = await get_gmail_client(db, user_id, org_id)
    if not client:
        raise Exception("Gmail not connected")
    
    return client.get_message(message_id)


async def send_email(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    to: str,
    subject: str,
    body: str
) -> Dict[str, Any]:
    """
    Send an email
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        to: Recipient email
        subject: Email subject
        body: Email body
        
    Returns:
        Sent message details
    """
    client = await get_gmail_client(db, user_id, org_id)
    if not client:
        raise Exception("Gmail not connected")
    
    return client.send_message(to, subject, body)


async def search_emails(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    query: str,
    max_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Search emails
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        query: Search query
        max_results: Maximum number of results
        
    Returns:
        List of matching emails
    """
    client = await get_gmail_client(db, user_id, org_id)
    if not client:
        raise Exception("Gmail not connected")
    
    return client.search_messages(query, max_results)
