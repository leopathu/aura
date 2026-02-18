"""
Jira Service
Provides Jira API functionality for managing issues and projects
"""

from typing import Optional, List, Dict, Any
from jira import JIRA
from jira.exceptions import JIRAError
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.credential import Credential
from app.services.credential_service import get_decrypted_api_key


class JiraClient:
    """Wrapper around Jira API"""
    
    def __init__(self, server: str, email: str, api_token: str):
        """
        Initialize Jira client with API credentials
        
        Args:
            server: Jira server URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            api_token: API token for authentication
        """
        self.client = JIRA(
            server=server,
            basic_auth=(email, api_token)
        )
        self.server = server
    
    def list_issues(
        self,
        jql: Optional[str] = None,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for issues using JQL (Jira Query Language)
        
        Args:
            jql: JQL query string (e.g., "project = PROJ AND status = Open")
            max_results: Maximum number of issues to return
            fields: List of fields to return
            
        Returns:
            List of issues
        """
        try:
            # Default fields if not specified
            if fields is None:
                fields = ['summary', 'status', 'assignee', 'priority', 'created', 'updated', 'description']
            
            # Default JQL to get recent issues
            if jql is None:
                jql = "ORDER BY updated DESC"
            
            # Search issues
            issues = self.client.search_issues(
                jql_str=jql,
                maxResults=max_results,
                fields=fields
            )
            
            # Format results
            formatted_issues = []
            for issue in issues:
                formatted_issue = {
                    "key": issue.key,
                    "id": issue.id,
                    "summary": issue.fields.summary,
                    "status": issue.fields.status.name if hasattr(issue.fields, 'status') else None,
                    "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                    "priority": issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
                    "created": str(issue.fields.created) if hasattr(issue.fields, 'created') else None,
                    "updated": str(issue.fields.updated) if hasattr(issue.fields, 'updated') else None,
                    "description": issue.fields.description if hasattr(issue.fields, 'description') else None,
                    "url": f"{self.server}/browse/{issue.key}"
                }
                formatted_issues.append(formatted_issue)
            
            return formatted_issues
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific issue
        
        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            
        Returns:
            Issue details
        """
        try:
            issue = self.client.issue(issue_key)
            
            # Get comments
            comments = []
            if hasattr(issue.fields, 'comment') and issue.fields.comment:
                for comment in issue.fields.comment.comments:
                    comments.append({
                        "author": comment.author.displayName if hasattr(comment, 'author') else "Unknown",
                        "body": comment.body,
                        "created": str(comment.created) if hasattr(comment, 'created') else None
                    })
            
            return {
                "key": issue.key,
                "id": issue.id,
                "summary": issue.fields.summary,
                "description": issue.fields.description if hasattr(issue.fields, 'description') else None,
                "status": issue.fields.status.name if hasattr(issue.fields, 'status') else None,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else "Unassigned",
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else "Unknown",
                "priority": issue.fields.priority.name if hasattr(issue.fields, 'priority') and issue.fields.priority else None,
                "created": str(issue.fields.created) if hasattr(issue.fields, 'created') else None,
                "updated": str(issue.fields.updated) if hasattr(issue.fields, 'updated') else None,
                "project": issue.fields.project.key if hasattr(issue.fields, 'project') else None,
                "issue_type": issue.fields.issuetype.name if hasattr(issue.fields, 'issuetype') else None,
                "comments": comments,
                "url": f"{self.server}/browse/{issue.key}"
            }
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def create_issue(
        self,
        project_key: str,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create a new Jira issue
        
        Args:
            project_key: Project key (e.g., "PROJ")
            summary: Issue summary/title
            description: Issue description
            issue_type: Issue type (Task, Bug, Story, etc.)
            assignee: Assignee username or email
            priority: Priority level
            
        Returns:
            Created issue details
        """
        try:
            # Build issue dict
            issue_dict = {
                'project': {'key': project_key},
                'summary': summary,
                'issuetype': {'name': issue_type}
            }
            
            if description:
                issue_dict['description'] = description
            
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            
            if priority:
                issue_dict['priority'] = {'name': priority}
            
            # Create issue
            new_issue = self.client.create_issue(fields=issue_dict)
            
            return {
                "key": new_issue.key,
                "id": new_issue.id,
                "summary": summary,
                "url": f"{self.server}/browse/{new_issue.key}"
            }
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def update_issue(
        self,
        issue_key: str,
        summary: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing Jira issue
        
        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            summary: New summary
            description: New description
            assignee: New assignee
            priority: New priority
            
        Returns:
            Updated issue details
        """
        try:
            issue = self.client.issue(issue_key)
            
            # Build update dict
            update_dict = {}
            
            if summary is not None:
                update_dict['summary'] = summary
            
            if description is not None:
                update_dict['description'] = description
            
            if assignee is not None:
                update_dict['assignee'] = {'name': assignee}
            
            if priority is not None:
                update_dict['priority'] = {'name': priority}
            
            # Update issue
            issue.update(fields=update_dict)
            
            return {
                "key": issue_key,
                "updated": True,
                "url": f"{self.server}/browse/{issue_key}"
            }
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """
        Add a comment to an issue
        
        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            comment: Comment text
            
        Returns:
            Comment details
        """
        try:
            issue = self.client.issue(issue_key)
            new_comment = self.client.add_comment(issue, comment)
            
            return {
                "issue_key": issue_key,
                "comment_id": new_comment.id,
                "body": comment,
                "created": str(new_comment.created) if hasattr(new_comment, 'created') else None
            }
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def transition_issue(
        self,
        issue_key: str,
        transition_name: str
    ) -> Dict[str, Any]:
        """
        Transition an issue to a new status
        
        Args:
            issue_key: Issue key (e.g., "PROJ-123")
            transition_name: Name of transition (e.g., "Done", "In Progress")
            
        Returns:
            Transition result
        """
        try:
            issue = self.client.issue(issue_key)
            
            # Get available transitions
            transitions = self.client.transitions(issue)
            
            # Find matching transition
            transition_id = None
            for transition in transitions:
                if transition['name'].lower() == transition_name.lower():
                    transition_id = transition['id']
                    break
            
            if transition_id is None:
                available = [t['name'] for t in transitions]
                raise Exception(f"Transition '{transition_name}' not found. Available: {', '.join(available)}")
            
            # Execute transition
            self.client.transition_issue(issue, transition_id)
            
            return {
                "issue_key": issue_key,
                "transition": transition_name,
                "success": True
            }
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")
    
    def get_projects(self) -> List[Dict[str, Any]]:
        """
        Get list of projects accessible by user
        
        Returns:
            List of projects
        """
        try:
            projects = self.client.projects()
            
            formatted_projects = []
            for project in projects:
                formatted_projects.append({
                    "key": project.key,
                    "name": project.name,
                    "id": project.id,
                    "url": f"{self.server}/browse/{project.key}"
                })
            
            return formatted_projects
        
        except JIRAError as error:
            raise Exception(f"Jira API error: {error.text}")


async def get_jira_client(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> JiraClient:
    """
    Get Jira client for user with stored credentials
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        JiraClient instance
        
    Raises:
        Exception if no valid Jira credentials found
    """
    # Get Jira credentials (org-level)
    credentials = db.query(Credential).filter(
        Credential.org_id == org_id,
        Credential.credential_type == "jira"
    ).first()
    
    if not credentials:
        raise Exception("No Jira credentials found. Please add Jira credentials in settings.")
    
    # Decrypt API key (format: server|email|token)
    from app.services.encryption_service import encryption_service
    decrypted = encryption_service.decrypt(credentials.encrypted_value)
    
    try:
        parts = decrypted.split("|")
        if len(parts) != 3:
            raise ValueError("Invalid Jira credentials format. Expected: server|email|token")
        
        server, email, api_token = parts
        
        # Create and return client
        return JiraClient(server, email, api_token)
    
    except Exception as e:
        raise Exception(f"Failed to parse Jira credentials: {str(e)}")


# Convenience async functions

async def search_jira_issues(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    jql: Optional[str] = None,
    max_results: int = 50
) -> List[Dict[str, Any]]:
    """
    Search Jira issues
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        jql: JQL query
        max_results: Max results
        
    Returns:
        List of issues
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.list_issues(jql, max_results)


async def get_jira_issue(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    issue_key: str
) -> Dict[str, Any]:
    """
    Get Jira issue details
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        issue_key: Issue key
        
    Returns:
        Issue details
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.get_issue(issue_key)


async def create_jira_issue(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    project_key: str,
    summary: str,
    description: Optional[str] = None,
    issue_type: str = "Task",
    assignee: Optional[str] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create Jira issue
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        project_key: Project key
        summary: Issue summary
        description: Issue description
        issue_type: Issue type
        assignee: Assignee
        priority: Priority
        
    Returns:
        Created issue
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.create_issue(
        project_key, summary, description,
        issue_type, assignee, priority
    )


async def update_jira_issue(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    issue_key: str,
    summary: Optional[str] = None,
    description: Optional[str] = None,
    assignee: Optional[str] = None,
    priority: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update Jira issue
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        issue_key: Issue key
        summary: New summary
        description: New description
        assignee: New assignee
        priority: New priority
        
    Returns:
        Update result
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.update_issue(
        issue_key, summary, description,
        assignee, priority
    )


async def add_jira_comment(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    issue_key: str,
    comment: str
) -> Dict[str, Any]:
    """
    Add comment to Jira issue
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        issue_key: Issue key
        comment: Comment text
        
    Returns:
        Comment details
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.add_comment(issue_key, comment)


async def transition_jira_issue(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    issue_key: str,
    transition_name: str
) -> Dict[str, Any]:
    """
    Transition Jira issue
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        issue_key: Issue key
        transition_name: Transition name
        
    Returns:
        Transition result
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.transition_issue(issue_key, transition_name)


async def get_jira_projects(
    db: Session,
    user_id: UUID,
    org_id: UUID
) -> List[Dict[str, Any]]:
    """
    Get Jira projects
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        List of projects
    """
    client = await get_jira_client(db, user_id, org_id)
    return client.get_projects()
