"""
Agent Tools Module
Provides tools for AI agents to interact with external services
"""

from typing import List, Dict, Optional
from langchain.tools import BaseTool
from sqlalchemy.orm import Session
from uuid import UUID

from app.tools.gmail_tools import get_gmail_tools
from app.services.oauth_service import get_oauth_token


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
        
        # Future: Add more integrations
        # - Google Calendar tools
        # - Slack tools
        # - Jira tools
        # - Notion tools
        
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
        
        return descriptions


__all__ = [
    "ToolRegistry",
    "get_gmail_tools"
]
