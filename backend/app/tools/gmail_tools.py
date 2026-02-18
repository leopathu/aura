"""
Gmail LangChain Tools
Tools for AI agents to interact with Gmail
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.services import gmail_service


class ListEmailsInput(BaseModel):
    """Input for list emails tool"""
    max_results: int = Field(default=10, description="Maximum number of emails to list")
    query: Optional[str] = Field(default=None, description="Gmail search query (e.g., 'from:user@example.com is:unread')")


class ListEmailsTool(BaseTool):
    """Tool for listing Gmail emails"""
    
    name: str = "list_emails"
    description: str = """
    List emails from Gmail inbox.
    Use this to get recent emails or search for specific emails.
    Returns email subjects, senders, dates, and snippets.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, max_results: int = 10, query: Optional[str] = None) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            emails = asyncio.run(gmail_service.list_emails(
                self.db,
                self.user_id,
                self.org_id,
                max_results,
                query
            ))
            
            if not emails:
                return "No emails found."
            
            # Format results
            result = f"Found {len(emails)} email(s):\n\n"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Snippet: {email['snippet'][:100]}...\n"
                result += f"   ID: {email['id']}\n\n"
            
            return result
        
        except Exception as e:
            return f"Error listing emails: {str(e)}"
    
    async def _arun(self, max_results: int = 10, query: Optional[str] = None) -> str:
        """Async execution"""
        return self._run(max_results, query)


class ReadEmailInput(BaseModel):
    """Input for read email tool"""
    message_id: str = Field(description="The ID of the email message to read")


class ReadEmailTool(BaseTool):
    """Tool for reading a specific Gmail email"""
    
    name: str = "read_email"
    description: str = """
    Read the full content of a specific email by its ID.
    Use this when you need to read the complete email body.
    Requires the message ID from list_emails.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, message_id: str) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            email = asyncio.run(gmail_service.read_email(
                self.db,
                self.user_id,
                self.org_id,
                message_id
            ))
            
            if not email:
                return "Email not found."
            
            # Format result
            result = f"Email Details:\n\n"
            result += f"From: {email['from']}\n"
            result += f"To: {email['to']}\n"
            result += f"Subject: {email['subject']}\n"
            result += f"Date: {email['date']}\n"
            result += f"\nBody:\n{email['body']}\n"
            
            return result
        
        except Exception as e:
            return f"Error reading email: {str(e)}"
    
    async def _arun(self, message_id: str) -> str:
        """Async execution"""
        return self._run(message_id)


class SendEmailInput(BaseModel):
    """Input for send email tool"""
    to: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")


class SendEmailTool(BaseTool):
    """Tool for sending Gmail emails"""
    
    name: str = "send_email"
    description: str = """
    Send an email via Gmail.
    Use this to compose and send emails to recipients.
    Returns confirmation when email is sent successfully.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, to: str, subject: str, body: str) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            result = asyncio.run(gmail_service.send_email(
                self.db,
                self.user_id,
                self.org_id,
                to,
                subject,
                body
            ))
            
            return f"Email sent successfully to {to}. Message ID: {result['id']}"
        
        except Exception as e:
            return f"Error sending email: {str(e)}"
    
    async def _arun(self, to: str, subject: str, body: str) -> str:
        """Async execution"""
        return self._run(to, subject, body)


class SearchEmailsInput(BaseModel):
    """Input for search emails tool"""
    query: str = Field(description="Gmail search query (e.g., 'from:user@example.com subject:important')")
    max_results: int = Field(default=10, description="Maximum number of results")


class SearchEmailsTool(BaseTool):
    """Tool for searching Gmail emails"""
    
    name: str = "search_emails"
    description: str = """
    Search emails in Gmail using advanced search queries.
    Supports Gmail search operators like from:, to:, subject:, is:unread, etc.
    Returns matching emails with subjects, senders, and snippets.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, query: str, max_results: int = 10) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            emails = asyncio.run(gmail_service.search_emails(
                self.db,
                self.user_id,
                self.org_id,
                query,
                max_results
            ))
            
            if not emails:
                return f"No emails found matching query: {query}"
            
            # Format results
            result = f"Found {len(emails)} email(s) matching '{query}':\n\n"
            for i, email in enumerate(emails, 1):
                result += f"{i}. From: {email['from']}\n"
                result += f"   Subject: {email['subject']}\n"
                result += f"   Date: {email['date']}\n"
                result += f"   Snippet: {email['snippet'][:100]}...\n"
                result += f"   ID: {email['id']}\n\n"
            
            return result
        
        except Exception as e:
            return f"Error searching emails: {str(e)}"
    
    async def _arun(self, query: str, max_results: int = 10) -> str:
        """Async execution"""
        return self._run(query, max_results)


def get_gmail_tools(db: Session, user_id: UUID, org_id: UUID) -> List[BaseTool]:
    """
    Get all Gmail tools for an agent
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        List of Gmail tools
    """
    return [
        ListEmailsTool(db=db, user_id=user_id, org_id=org_id),
        ReadEmailTool(db=db, user_id=user_id, org_id=org_id),
        SendEmailTool(db=db, user_id=user_id, org_id=org_id),
        SearchEmailsTool(db=db, user_id=user_id, org_id=org_id)
    ]
