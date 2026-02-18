"""
Trigger Service

Service for handling event-based triggers for automations

TASK-334: Create webhook endpoint for triggers
TASK-335: Add trigger condition evaluation
TASK-336: Create event matching logic
TASK-337: Add trigger authentication
TASK-338: Create trigger logging
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
import hmac
import hashlib
import json

from app.models.automation import Automation, AutomationRun, TriggerType, AutomationStatus


class TriggerConditionEvaluator:
    """
    Evaluate trigger conditions against event data
    
    TASK-335: Trigger condition evaluation
    """
    
    @staticmethod
    def evaluate(condition: Dict[str, Any], event_data: Dict[str, Any]) -> bool:
        """
        Evaluate a condition against event data
        
        Supported operators:
        - equals: exact match
        - not_equals: not equal
        - contains: string contains
        - not_contains: string does not contain
        - greater_than: numeric comparison
        - less_than: numeric comparison
        - in: value in list
        - not_in: value not in list
        - exists: field exists
        - not_exists: field does not exist
        
        Args:
            condition: Condition definition
            event_data: Event data to evaluate
        
        Returns:
            True if condition matches, False otherwise
        """
        if not condition:
            return True  # No condition means always match
        
        operator = condition.get("operator")
        field = condition.get("field")
        value = condition.get("value")
        
        if not operator or not field:
            return False
        
        # Get field value from event data (supports nested fields with dot notation)
        field_value = TriggerConditionEvaluator._get_nested_value(event_data, field)
        
        # Evaluate based on operator
        if operator == "equals":
            return field_value == value
        
        elif operator == "not_equals":
            return field_value != value
        
        elif operator == "contains":
            return value in str(field_value) if field_value is not None else False
        
        elif operator == "not_contains":
            return value not in str(field_value) if field_value is not None else True
        
        elif operator == "greater_than":
            try:
                return float(field_value) > float(value)
            except (TypeError, ValueError):
                return False
        
        elif operator == "less_than":
            try:
                return float(field_value) < float(value)
            except (TypeError, ValueError):
                return False
        
        elif operator == "in":
            return field_value in value if isinstance(value, list) else False
        
        elif operator == "not_in":
            return field_value not in value if isinstance(value, list) else True
        
        elif operator == "exists":
            return field_value is not None
        
        elif operator == "not_exists":
            return field_value is None
        
        return False
    
    @staticmethod
    def _get_nested_value(data: Dict[str, Any], field_path: str) -> Any:
        """
        Get nested value from dictionary using dot notation
        
        Args:
            data: Dictionary to search
            field_path: Dot-separated field path (e.g., "user.email")
        
        Returns:
            Field value or None if not found
        """
        keys = field_path.split(".")
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        
        return value
    
    @staticmethod
    def evaluate_multiple(
        conditions: List[Dict[str, Any]], 
        event_data: Dict[str, Any],
        logic: str = "AND"
    ) -> bool:
        """
        Evaluate multiple conditions with AND/OR logic
        
        Args:
            conditions: List of conditions
            event_data: Event data
            logic: "AND" or "OR"
        
        Returns:
            True if conditions match, False otherwise
        """
        if not conditions:
            return True
        
        results = [
            TriggerConditionEvaluator.evaluate(cond, event_data) 
            for cond in conditions
        ]
        
        if logic == "OR":
            return any(results)
        else:  # Default to AND
            return all(results)


class EventMatcher:
    """
    Match events to automations
    
    TASK-336: Event matching logic
    """
    
    @staticmethod
    def find_matching_automations(
        db: Session,
        event_type: str,
        event_data: Dict[str, Any],
        org_id: str
    ) -> List[Automation]:
        """
        Find automations that match the given event
        
        Args:
            db: Database session
            event_type: Type of event (e.g., "agent.completed", "email.received")
            event_data: Event data
            org_id: Organization ID
        
        Returns:
            List of matching automations
        """
        # Query active EVENT-type automations for this org
        automations = db.query(Automation).filter(
            and_(
                Automation.org_id == org_id,
                Automation.trigger_type == TriggerType.EVENT,
                Automation.status == AutomationStatus.ACTIVE
            )
        ).all()
        
        matching = []
        
        for automation in automations:
            if EventMatcher._matches_event(automation, event_type, event_data):
                matching.append(automation)
        
        return matching
    
    @staticmethod
    def _matches_event(
        automation: Automation,
        event_type: str,
        event_data: Dict[str, Any]
    ) -> bool:
        """
        Check if automation matches event
        
        Args:
            automation: Automation to check
            event_type: Event type
            event_data: Event data
        
        Returns:
            True if matches, False otherwise
        """
        trigger_config = automation.trigger_config or {}
        
        # Check event type
        configured_event_type = trigger_config.get("event_type")
        if configured_event_type and configured_event_type != event_type:
            return False
        
        # Check conditions
        conditions = trigger_config.get("conditions", [])
        logic = trigger_config.get("logic", "AND")
        
        return TriggerConditionEvaluator.evaluate_multiple(
            conditions, 
            event_data, 
            logic
        )


class WebhookAuthenticator:
    """
    Authenticate webhook requests
    
    TASK-337: Trigger authentication
    """
    
    @staticmethod
    def verify_signature(
        payload: bytes,
        signature: str,
        secret: str,
        algorithm: str = "sha256"
    ) -> bool:
        """
        Verify webhook signature (HMAC)
        
        Args:
            payload: Request payload (bytes)
            signature: Provided signature
            secret: Webhook secret
            algorithm: Hash algorithm (sha256, sha1)
        
        Returns:
            True if signature is valid, False otherwise
        """
        if not secret or not signature:
            return False
        
        try:
            # Calculate expected signature
            if algorithm == "sha256":
                expected = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha256
                ).hexdigest()
            elif algorithm == "sha1":
                expected = hmac.new(
                    secret.encode(),
                    payload,
                    hashlib.sha1
                ).hexdigest()
            else:
                return False
            
            # Compare signatures (constant-time comparison)
            return hmac.compare_digest(signature, expected)
        
        except Exception:
            return False
    
    @staticmethod
    def verify_api_key(provided_key: str, expected_key: str) -> bool:
        """
        Verify API key authentication
        
        Args:
            provided_key: Provided API key
            expected_key: Expected API key
        
        Returns:
            True if keys match, False otherwise
        """
        if not provided_key or not expected_key:
            return False
        
        return hmac.compare_digest(provided_key, expected_key)


class TriggerLogger:
    """
    Log trigger events
    
    TASK-338: Trigger logging
    """
    
    @staticmethod
    def log_webhook_received(
        automation_id: str,
        event_type: str,
        event_data: Dict[str, Any],
        source_ip: Optional[str] = None,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """
        Create log entry for webhook received
        
        Args:
            automation_id: Automation ID
            event_type: Event type
            event_data: Event data
            source_ip: Source IP address
            authenticated: Whether request was authenticated
        
        Returns:
            Log entry
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "automation_id": automation_id,
            "event_type": event_type,
            "event_data_keys": list(event_data.keys()),
            "source_ip": source_ip,
            "authenticated": authenticated,
            "log_type": "webhook_received"
        }
    
    @staticmethod
    def log_trigger_matched(
        automation_id: str,
        event_type: str,
        conditions_matched: bool,
        matched_count: int = 1
    ) -> Dict[str, Any]:
        """
        Create log entry for trigger match
        
        Args:
            automation_id: Automation ID
            event_type: Event type
            conditions_matched: Whether conditions matched
            matched_count: Number of automations matched
        
        Returns:
            Log entry
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "automation_id": automation_id,
            "event_type": event_type,
            "conditions_matched": conditions_matched,
            "matched_count": matched_count,
            "log_type": "trigger_matched"
        }
    
    @staticmethod
    def log_trigger_failed(
        automation_id: str,
        event_type: str,
        error: str,
        authenticated: bool = False
    ) -> Dict[str, Any]:
        """
        Create log entry for trigger failure
        
        Args:
            automation_id: Automation ID
            event_type: Event type
            error: Error message
            authenticated: Whether request was authenticated
        
        Returns:
            Log entry
        """
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "automation_id": automation_id,
            "event_type": event_type,
            "error": error,
            "authenticated": authenticated,
            "log_type": "trigger_failed"
        }


def trigger_event(
    db: Session,
    org_id: str,
    event_type: str,
    event_data: Dict[str, Any]
) -> List[str]:
    """
    Trigger event and find matching automations
    
    TASK-336: Event matching logic
    
    Args:
        db: Database session
        org_id: Organization ID
        event_type: Event type
        event_data: Event data
    
    Returns:
        List of task IDs for triggered automations
    """
    from app.tasks.automation_tasks import execute_automation
    
    # Find matching automations
    automations = EventMatcher.find_matching_automations(
        db, event_type, event_data, org_id
    )
    
    task_ids = []
    
    for automation in automations:
        # Queue automation execution
        task = execute_automation.delay(
            str(automation.id),
            trigger_type=TriggerType.EVENT.value,
            trigger_data={
                "event_type": event_type,
                "event_data": event_data,
                "triggered_at": datetime.utcnow().isoformat()
            }
        )
        task_ids.append(task.id)
    
    return task_ids
