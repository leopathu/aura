"""
Jira LangChain Tools
Tools for AI agents to interact with Jira
"""

from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session
from uuid import UUID

from app.services import jira_service


class SearchIssuesInput(BaseModel):
    """Input for search issues tool"""
    jql: Optional[str] = Field(default=None, description="JQL query (e.g., 'project = PROJ AND status = Open'). If not provided, returns recent issues.")
    max_results: int = Field(default=20, description="Maximum number of issues to return")


class SearchIssuesTool(BaseTool):
    """Tool for searching Jira issues"""
    
    name: str = "search_jira_issues"
    description: str = """
    Search for Jira issues using JQL (Jira Query Language).
    Use this to find issues, filter by project, status, assignee, etc.
    Returns issue keys, summaries, status, assignee, and priority.
    
    Example JQL queries:
    - "project = PROJ" - All issues in project PROJ
    - "assignee = currentUser()" - Issues assigned to you
    - "status = 'In Progress'" - Issues in progress
    - "project = PROJ AND status = Open" - Open issues in PROJ
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, jql: Optional[str] = None, max_results: int = 20) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            issues = asyncio.run(jira_service.search_jira_issues(
                self.db,
                self.user_id,
                self.org_id,
                jql,
                max_results
            ))
            
            if not issues:
                return "No issues found." if jql else "No recent issues found."
            
            # Format results
            result = f"Found {len(issues)} issue(s):\n\n"
            for i, issue in enumerate(issues, 1):
                result += f"{i}. [{issue['key']}] {issue['summary']}\n"
                result += f"   Status: {issue['status']}\n"
                result += f"   Assignee: {issue['assignee']}\n"
                
                if issue['priority']:
                    result += f"   Priority: {issue['priority']}\n"
                
                if issue['description']:
                    desc = issue['description'][:100]
                    result += f"   Description: {desc}{'...' if len(issue['description']) > 100 else ''}\n"
                
                result += f"   URL: {issue['url']}\n\n"
            
            return result
        
        except Exception as e:
            return f"Error searching Jira issues: {str(e)}"
    
    async def _arun(self, jql: Optional[str] = None, max_results: int = 20) -> str:
        """Async execution"""
        return self._run(jql, max_results)


class GetIssueInput(BaseModel):
    """Input for get issue tool"""
    issue_key: str = Field(description="The Jira issue key (e.g., 'PROJ-123')")


class GetIssueTool(BaseTool):
    """Tool for getting detailed information about a Jira issue"""
    
    name: str = "get_jira_issue"
    description: str = """
    Get detailed information about a specific Jira issue by its key.
    Use this when you need full details including description, comments, and history.
    Requires the issue key from search_jira_issues.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(self, issue_key: str) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            issue = asyncio.run(jira_service.get_jira_issue(
                self.db,
                self.user_id,
                self.org_id,
                issue_key
            ))
            
            # Format result
            result = f"Issue Details: [{issue['key']}]\n\n"
            result += f"Summary: {issue['summary']}\n"
            result += f"Status: {issue['status']}\n"
            result += f"Assignee: {issue['assignee']}\n"
            result += f"Reporter: {issue['reporter']}\n"
            
            if issue['priority']:
                result += f"Priority: {issue['priority']}\n"
            
            result += f"Type: {issue['issue_type']}\n"
            result += f"Project: {issue['project']}\n"
            result += f"Created: {issue['created']}\n"
            result += f"Updated: {issue['updated']}\n"
            
            if issue['description']:
                result += f"\nDescription:\n{issue['description']}\n"
            
            if issue['comments']:
                result += f"\nComments ({len(issue['comments'])}):\n"
                for comment in issue['comments'][:5]:  # Show first 5 comments
                    result += f"- {comment['author']}: {comment['body'][:100]}...\n"
                if len(issue['comments']) > 5:
                    result += f"  ... and {len(issue['comments']) - 5} more comments\n"
            
            result += f"\nURL: {issue['url']}\n"
            
            return result
        
        except Exception as e:
            return f"Error getting Jira issue: {str(e)}"
    
    async def _arun(self, issue_key: str) -> str:
        """Async execution"""
        return self._run(issue_key)


class CreateIssueInput(BaseModel):
    """Input for create issue tool"""
    project_key: str = Field(description="Project key (e.g., 'PROJ')")
    summary: str = Field(description="Issue summary/title")
    description: Optional[str] = Field(default=None, description="Issue description")
    issue_type: str = Field(default="Task", description="Issue type: Task, Bug, Story, etc.")
    assignee: Optional[str] = Field(default=None, description="Assignee username or email")
    priority: Optional[str] = Field(default=None, description="Priority: High, Medium, Low, etc.")


class CreateIssueTool(BaseTool):
    """Tool for creating a new Jira issue"""
    
    name: str = "create_jira_issue"
    description: str = """
    Create a new Jira issue in a project.
    Use this to create tasks, bugs, stories, etc.
    Requires project key and summary at minimum.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(
        self,
        project_key: str,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            issue = asyncio.run(jira_service.create_jira_issue(
                self.db,
                self.user_id,
                self.org_id,
                project_key,
                summary,
                description,
                issue_type,
                assignee,
                priority
            ))
            
            result = f"✓ Jira issue created successfully!\n\n"
            result += f"Key: {issue['key']}\n"
            result += f"Summary: {issue['summary']}\n"
            result += f"URL: {issue['url']}\n"
            
            return result
        
        except Exception as e:
            return f"Error creating Jira issue: {str(e)}"
    
    async def _arun(
        self,
        project_key: str,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """Async execution"""
        return self._run(project_key, summary, description, issue_type, assignee, priority)


class UpdateIssueInput(BaseModel):
    """Input for update issue tool"""
    issue_key: str = Field(description="The issue key to update (e.g., 'PROJ-123')")
    summary: Optional[str] = Field(default=None, description="New summary")
    description: Optional[str] = Field(default=None, description="New description")
    assignee: Optional[str] = Field(default=None, description="New assignee")
    priority: Optional[str] = Field(default=None, description="New priority")


class UpdateIssueTool(BaseTool):
    """Tool for updating an existing Jira issue"""
    
    name: str = "update_jira_issue"
    description: str = """
    Update an existing Jira issue.
    Use this to change summary, description, assignee, or priority.
    Requires the issue key from search_jira_issues or get_jira_issue.
    """
    
    db: Session
    user_id: UUID
    org_id: UUID
    
    class Config:
        arbitrary_types_allowed = True
    
    def _run(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """Execute the tool"""
        try:
            # Use async wrapper
            import asyncio
            result = asyncio.run(jira_service.update_jira_issue(
                self.db,
                self.user_id,
                self.org_id,
                issue_key,
                summary,
                description,
                assignee,
                priority
            ))
            
            response = f"✓ Jira issue {issue_key} updated successfully!\n"
            response += f"URL: {result['url']}\n"
            
            return response
        
        except Exception as e:
            return f"Error updating Jira issue: {str(e)}"
    
    async def _arun(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> str:
        """Async execution"""
        return self._run(issue_key, summary, description, assignee, priority)


def get_jira_tools(db: Session, user_id: UUID, org_id: UUID) -> List[BaseTool]:
    """
    Get all Jira tools for an agent
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        List of Jira tools
    """
    return [
        SearchIssuesTool(db=db, user_id=user_id, org_id=org_id),
        GetIssueTool(db=db, user_id=user_id, org_id=org_id),
        CreateIssueTool(db=db, user_id=user_id, org_id=org_id),
        UpdateIssueTool(db=db, user_id=user_id, org_id=org_id)
    ]
