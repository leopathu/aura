"""
Agent Tools Module
Provides tools for AI agents to interact with external services
"""

from typing import List, Dict, Optional
from langchain.tools import BaseTool
from sqlalchemy.orm import Session
from uuid import UUID

from app.tools.gmail_tools import get_gmail_tools
from app.tools.calendar_tools import get_calendar_tools
from app.tools.jira_tools import get_jira_tools
from app.tools.slack_tools import get_slack_tools
from app.services.oauth_service import get_oauth_token
from app.models.credential import Credential


class ToolRegistry:
    """Registry for managing agent tools"""
    
    @staticmethod
    async def get_available_tools(
        db: Session,
        user_id: UUID,
        org_id: UUID
    ) -> List[BaseTool]:
        """
        Get all available tools for a user based on their connected integrations
        
        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            List of available tools
        """
        tools = []
        
        # Check Gmail connection
        gmail_token = await get_oauth_token(db, user_id, org_id, "google")
        if gmail_token and gmail_token.is_active:
            tools.extend(get_gmail_tools(db, user_id, org_id))
        
        # Check Calendar connection (uses same Google OAuth token)
        calendar_token = await get_oauth_token(db, user_id, org_id, "google")
        if calendar_token and calendar_token.is_active:
            tools.extend(get_calendar_tools(db, user_id, org_id))
        
        # Check Jira connection (uses API key credential)
        jira_cred = db.query(Credential).filter(
            Credential.org_id == org_id,
            Credential.credential_type == "jira",
            Credential.is_active == True
        ).first()
        if jira_cred:
            tools.extend(get_jira_tools(db, user_id, org_id))
        
        # Check Slack connection (uses OAuth token)
        slack_token = await get_oauth_token(db, user_id, org_id, "slack")
        if slack_token and slack_token.is_active:
            tools.extend(get_slack_tools(db, user_id, org_id))
        
        return tools
    
    @staticmethod
    async def get_tools_by_category(
        db: Session,
        user_id: UUID,
        org_id: UUID,
        category: str
    ) -> List[BaseTool]:
        """
        Get tools for a specific category/integration
        
        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            category: Tool category (e.g., 'gmail', 'calendar', 'slack')
            
        Returns:
            List of tools for the category
        """
        if category.lower() == "gmail":
            gmail_token = await get_oauth_token(db, user_id, org_id, "google")
            if gmail_token and gmail_token.is_active:
                return get_gmail_tools(db, user_id, org_id)
        
        elif category.lower() == "calendar":
            calendar_token = await get_oauth_token(db, user_id, org_id, "google")
            if calendar_token and calendar_token.is_active:
                return get_calendar_tools(db, user_id, org_id)
        
        elif category.lower() == "jira":
            jira_cred = db.query(Credential).filter(
                Credential.org_id == org_id,
                Credential.credential_type == "jira",
                Credential.is_active == True
            ).first()
            if jira_cred:
                return get_jira_tools(db, user_id, org_id)
        
        elif category.lower() == "slack":
            slack_token = await get_oauth_token(db, user_id, org_id, "slack")
            if slack_token and slack_token.is_active:
                return get_slack_tools(db, user_id, org_id)
        
        return []
    
    @staticmethod
    async def get_tool_descriptions(
        db: Session,
        user_id: UUID,
        org_id: UUID
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get descriptions of all available tools grouped by category
        
        Args:
            db: Database session
            user_id: User ID
            org_id: Organization ID
            
        Returns:
            Dictionary mapping category to tool descriptions
        """
        descriptions = {}
        
        # Gmail tools
        gmail_token = await get_oauth_token(db, user_id, org_id, "google")
        if gmail_token and gmail_token.is_active:
            descriptions["gmail"] = [
                {"name": "list_emails", "description": "List recent emails from Gmail inbox"},
                {"name": "read_email", "description": "Read the full content of a specific email"},
                {"name": "send_email", "description": "Send an email via Gmail"},
                {"name": "search_emails", "description": "Search emails using Gmail search queries"}
            ]
        
        # Calendar tools
        calendar_token = await get_oauth_token(db, user_id, org_id, "google")
        if calendar_token and calendar_token.is_active:
            descriptions["calendar"] = [
                {"name": "list_calendar_events", "description": "List upcoming calendar events"},
                {"name": "create_calendar_event", "description": "Create a new calendar event"},
                {"name": "update_calendar_event", "description": "Update an existing calendar event"}
            ]
        
        # Jira tools
        jira_cred = db.query(Credential).filter(
            Credential.org_id == org_id,
            Credential.credential_type == "jira",
            Credential.is_active == True
        ).first()
        if jira_cred:
            descriptions["jira"] = [
                {"name": "search_jira_issues", "description": "Search Jira issues using JQL"},
                {"name": "get_jira_issue", "description": "Get detailed information about a Jira issue"},
                {"name": "create_jira_issue", "description": "Create a new Jira issue"},
                {"name": "update_jira_issue", "description": "Update an existing Jira issue"}
            ]
        
        # Slack tools
        slack_token = await get_oauth_token(db, user_id, org_id, "slack")
        if slack_token and slack_token.is_active:
            descriptions["slack"] = [
                {"name": "send_slack_message", "description": "Send a message to a Slack channel or thread"},
                {"name": "read_slack_messages", "description": "Read message history from a Slack channel"},
                {"name": "list_slack_channels", "description": "List all available Slack channels"}
            ]
        
        return descriptions


__all__ = [
    "ToolRegistry",
    "get_gmail_tools",
    "get_calendar_tools",
    "get_jira_tools",
    "get_slack_tools"
]
