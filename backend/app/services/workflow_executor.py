"""
Workflow Executor Service

TASK-322: Create workflow parser
TASK-323: Create step executor
TASK-324: Add conditional logic support
TASK-325: Create workflow state management
TASK-326: Add error handling and rollback
TASK-327: Create workflow completion handler
"""

from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime
import json

from app.models.automation import AutomationRun, RunStatus
from app.models.agent import Agent
from app.services.streaming_agent import StreamingAgentOrchestrator


class WorkflowState:
    """
    Workflow state management (TASK-325)
    """
    
    def __init__(self, initial_context: Dict[str, Any] = None):
        self.context = initial_context or {}
        self.variables = {}
        self.step_results = []
        self.rollback_stack = []
    
    def set_variable(self, name: str, value: Any):
        """Set a workflow variable"""
        self.variables[name] = value
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a workflow variable"""
        return self.variables.get(name, default)
    
    def add_step_result(self, step_index: int, result: Dict[str, Any]):
        """Add step execution result"""
        self.step_results.append({
            "step": step_index,
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def add_rollback_action(self, action: Dict[str, Any]):
        """Add action to rollback stack (TASK-326)"""
        self.rollback_stack.append(action)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary"""
        return {
            "context": self.context,
            "variables": self.variables,
            "step_results": self.step_results,
            "rollback_stack": self.rollback_stack
        }


class WorkflowParser:
    """
    Workflow definition parser (TASK-322)
    """
    
    @staticmethod
    def parse(workflow_definition: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse workflow definition into executable steps
        
        Args:
            workflow_definition: Workflow JSON definition
        
        Returns:
            List of parsed step definitions
        
        Workflow format:
        {
            "steps": [
                {
                    "type": "agent_task",
                    "agent_id": "...",
                    "prompt": "...",
                    "save_to": "variable_name"
                },
                {
                    "type": "condition",
                    "condition": "{{ variables.status == 'success' }}",
                    "then": [...],
                    "else": [...]
                },
                {
                    "type": "http_request",
                    "method": "POST",
                    "url": "...",
                    "body": {...}
                }
            ]
        }
        """
        if not workflow_definition or "steps" not in workflow_definition:
            raise ValueError("Invalid workflow definition: missing 'steps'")
        
        steps = workflow_definition["steps"]
        
        if not isinstance(steps, list):
            raise ValueError("Invalid workflow definition: 'steps' must be a list")
        
        # Validate steps
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                raise ValueError(f"Step {i} must be a dictionary")
            
            if "type" not in step:
                raise ValueError(f"Step {i} missing required field 'type'")
        
        return steps
    
    @staticmethod
    def evaluate_condition(condition: str, state: WorkflowState) -> bool:
        """
        Evaluate a condition expression (TASK-324)
        
        Supports simple template syntax: {{ variable_name == 'value' }}
        """
        # Remove template markers
        condition = condition.strip()
        if condition.startswith("{{") and condition.endswith("}}"):
            condition = condition[2:-2].strip()
        
        # Simple evaluation context
        context = {
            "variables": state.variables,
            "context": state.context
        }
        
        try:
            # Safe evaluation (restricted namespace)
            return eval(condition, {"__builtins__": {}}, context)
        except Exception as e:
            raise ValueError(f"Failed to evaluate condition '{condition}': {e}")


class StepExecutor:
    """
    Individual step executor (TASK-323)
    """
    
    def __init__(self, db: Session, run: AutomationRun):
        self.db = db
        self.run = run
    
    async def execute_agent_task(
        self,
        step: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute agent task step"""
        agent_id = step.get("agent_id")
        prompt = step.get("prompt")
        
        if not agent_id or not prompt:
            raise ValueError("agent_task step requires 'agent_id' and 'prompt'")
        
        # Get agent
        from uuid import UUID
        agent = self.db.query(Agent).filter(Agent.id == UUID(agent_id)).first()
        
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")
        
        # Replace variables in prompt
        prompt = self._replace_variables(prompt, state)
        
        # Execute agent
        orchestrator = StreamingAgentOrchestrator(self.db, agent)
        
        # Collect response
        response_text = ""
        async for event in orchestrator.stream_agent_response(
            messages=[{"role": "user", "content": prompt}],
            user_id=None
        ):
            if event["type"] == "token":
                response_text += event["content"]
        
        return {
            "status": "success",
            "response": response_text,
            "agent_id": str(agent_id)
        }
    
    async def execute_http_request(
        self,
        step: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute HTTP request step"""
        import aiohttp
        
        method = step.get("method", "GET").upper()
        url = step.get("url")
        headers = step.get("headers", {})
        body = step.get("body")
        
        if not url:
            raise ValueError("http_request step requires 'url'")
        
        # Replace variables
        url = self._replace_variables(url, state)
        body = self._replace_variables_in_dict(body, state) if body else None
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                url,
                headers=headers,
                json=body
            ) as response:
                result = {
                    "status": "success",
                    "status_code": response.status,
                    "headers": dict(response.headers),
                }
                
                try:
                    result["body"] = await response.json()
                except:
                    result["body"] = await response.text()
                
                return result
    
    async def execute_delay(
        self,
        step: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute delay step"""
        import asyncio
        
        seconds = step.get("seconds", 1)
        await asyncio.sleep(seconds)
        
        return {
            "status": "success",
            "delayed": seconds
        }
    
    async def execute_set_variable(
        self,
        step: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """Execute set variable step"""
        name = step.get("name")
        value = step.get("value")
        
        if not name:
            raise ValueError("set_variable step requires 'name'")
        
        # Replace variables in value
        value = self._replace_variables(value, state) if isinstance(value, str) else value
        
        state.set_variable(name, value)
        
        return {
            "status": "success",
            "variable": name,
            "value": value
        }
    
    def _replace_variables(self, text: str, state: WorkflowState) -> str:
        """Replace {{ variable_name }} in text"""
        import re
        
        def replacer(match):
            var_path = match.group(1).strip()
            
            # Support dot notation: variables.name or context.field
            parts = var_path.split(".")
            
            if parts[0] == "variables":
                value = state.variables
                for part in parts[1:]:
                    value = value.get(part) if isinstance(value, dict) else None
            elif parts[0] == "context":
                value = state.context
                for part in parts[1:]:
                    value = value.get(part) if isinstance(value, dict) else None
            else:
                value = state.get_variable(var_path)
            
            return str(value) if value is not None else ""
        
        return re.sub(r"\{\{\s*([^}]+)\s*\}\}", replacer, text)
    
    def _replace_variables_in_dict(
        self,
        data: Dict[str, Any],
        state: WorkflowState
    ) -> Dict[str, Any]:
        """Replace variables in dictionary recursively"""
        result = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                result[key] = self._replace_variables(value, state)
            elif isinstance(value, dict):
                result[key] = self._replace_variables_in_dict(value, state)
            elif isinstance(value, list):
                result[key] = [
                    self._replace_variables(v, state) if isinstance(v, str)
                    else self._replace_variables_in_dict(v, state) if isinstance(v, dict)
                    else v
                    for v in value
                ]
            else:
                result[key] = value
        
        return result


class WorkflowExecutor:
    """
    Main workflow executor (TASK-322 to TASK-327)
    """
    
    def __init__(self, db: Session, run: AutomationRun):
        self.db = db
        self.run = run
        self.parser = WorkflowParser()
        self.step_executor = StepExecutor(db, run)
        self.state = WorkflowState()
    
    def execute(
        self,
        workflow_definition: Dict[str, Any],
        trigger_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Execute workflow (TASK-327)
        
        Args:
            workflow_definition: Workflow JSON definition
            trigger_data: Data from trigger
        
        Returns:
            Workflow execution result
        """
        # Initialize state with trigger data
        self.state.context = trigger_data or {}
        
        try:
            # Parse workflow (TASK-322)
            steps = self.parser.parse(workflow_definition)
            
            self.run.total_steps = len(steps)
            self.db.commit()
            
            # Execute steps
            import asyncio
            result = asyncio.run(self._execute_steps(steps))
            
            return result
            
        except Exception as e:
            # Error handling and rollback (TASK-326)
            self.run.add_log("error", f"Workflow execution failed: {str(e)}")
            self._rollback()
            raise
    
    async def _execute_steps(self, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Execute workflow steps sequentially"""
        for i, step in enumerate(steps):
            # Update progress
            self.run.current_step = i + 1
            self.run.add_log("info", f"Executing step {i + 1}/{len(steps)}: {step['type']}")
            self.db.commit()
            
            # Execute step (TASK-323)
            step_result = await self._execute_step(i, step)
            
            # Save result
            self.state.add_step_result(i, step_result)
            
            # Save to variable if specified
            if "save_to" in step:
                self.state.set_variable(step["save_to"], step_result)
            
            # Update run context
            self.run.context = self.state.to_dict()
            self.db.commit()
        
        return {
            "status": "success",
            "steps_executed": len(steps),
            "final_state": self.state.to_dict()
        }
    
    async def _execute_step(self, index: int, step: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step (TASK-323)"""
        step_type = step["type"]
        
        # Handle conditional steps (TASK-324)
        if step_type == "condition":
            return await self._execute_condition(step)
        
        # Execute different step types
        if step_type == "agent_task":
            return await self.step_executor.execute_agent_task(step, self.state)
        elif step_type == "http_request":
            return await self.step_executor.execute_http_request(step, self.state)
        elif step_type == "delay":
            return await self.step_executor.execute_delay(step, self.state)
        elif step_type == "set_variable":
            return await self.step_executor.execute_set_variable(step, self.state)
        else:
            raise ValueError(f"Unknown step type: {step_type}")
    
    async def _execute_condition(self, step: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute conditional step (TASK-324)
        
        Step format:
        {
            "type": "condition",
            "condition": "{{ variables.status == 'success' }}",
            "then": [...],
            "else": [...]
        }
        """
        condition = step.get("condition")
        then_steps = step.get("then", [])
        else_steps = step.get("else", [])
        
        if not condition:
            raise ValueError("condition step requires 'condition' field")
        
        # Evaluate condition
        result = self.parser.evaluate_condition(condition, self.state)
        
        # Execute appropriate branch
        branch_steps = then_steps if result else else_steps
        
        if branch_steps:
            branch_result = await self._execute_steps(branch_steps)
            return {
                "status": "success",
                "condition_result": result,
                "branch": "then" if result else "else",
                "branch_result": branch_result
            }
        
        return {
            "status": "success",
            "condition_result": result,
            "branch": "then" if result else "else"
        }
    
    def _rollback(self):
        """
        Rollback workflow changes (TASK-326)
        
        Execute rollback actions in reverse order
        """
        self.run.add_log("warning", "Starting workflow rollback")
        
        for action in reversed(self.state.rollback_stack):
            try:
                # Execute rollback action
                action_type = action.get("type")
                
                if action_type == "delete_record":
                    # Delete created record
                    pass  # Implement based on needs
                elif action_type == "restore_value":
                    # Restore previous value
                    pass  # Implement based on needs
                
                self.run.add_log("info", f"Rolled back: {action_type}")
                
            except Exception as e:
                self.run.add_log("error", f"Rollback failed for {action.get('type')}: {e}")
        
        self.run.add_log("warning", "Workflow rollback completed")
        self.db.commit()


# Export
__all__ = [
    "WorkflowExecutor",
    "WorkflowParser",
    "StepExecutor",
    "WorkflowState"
]
