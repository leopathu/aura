"""
Automation Tasks

Celery tasks for automation execution and management
"""

from celery import current_task
from datetime import datetime, timedelta
from uuid import UUID
from typing import Dict, Any

from app.celery_config import celery_app, BaseTask
from app.db.session import SessionLocal
from app.models.automation import Automation, AutomationRun, RunStatus, AutomationStatus
from app.services.workflow_executor import WorkflowExecutor


@celery_app.task(base=BaseTask, bind=True, name="app.tasks.automation_tasks.execute_automation")
def execute_automation(self, automation_id: str, trigger_type: str, trigger_data: dict = None):
    """
    Execute an automation workflow
    
    Args:
        automation_id: Automation UUID
        trigger_type: Type of trigger (schedule, webhook, event, manual)
        trigger_data: Additional trigger data
    
    Returns:
        Automation run ID
    """
    db = SessionLocal()
    
    try:
        # Get automation
        automation = db.query(Automation).filter(
            Automation.id == UUID(automation_id)
        ).first()
        
        if not automation:
            raise ValueError(f"Automation {automation_id} not found")
        
        if automation.status != AutomationStatus.ACTIVE:
            raise ValueError(f"Automation {automation_id} is not active")
        
        # Create automation run
        run = AutomationRun(
            automation_id=automation.id,
            status=RunStatus.PENDING,
            trigger_type=trigger_type,
            trigger_data=trigger_data or {},
            task_id=self.request.id,
            context={}
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        # Update run status to running
        run.status = RunStatus.RUNNING
        run.started_at = datetime.utcnow()
        run.add_log("info", f"Starting automation: {automation.name}")
        db.commit()
        
        # Execute workflow
        executor = WorkflowExecutor(db, run)
        result = executor.execute(automation.workflow, trigger_data or {})
        
        # Update run with success
        run.status = RunStatus.SUCCESS
        run.completed_at = datetime.utcnow()
        run.result = result
        run.add_log("info", "Automation completed successfully")
        
        # Update automation statistics
        automation.last_run_at = datetime.utcnow()
        automation.total_runs += 1
        automation.success_runs += 1
        
        db.commit()
        
        return str(run.id)
        
    except Exception as e:
        # Update run with failure
        if 'run' in locals():
            run.status = RunStatus.FAILED
            run.completed_at = datetime.utcnow()
            run.error = str(e)
            run.add_log("error", f"Automation failed: {str(e)}")
            db.commit()
        
        # Update automation statistics
        if 'automation' in locals():
            automation.last_run_at = datetime.utcnow()
            automation.total_runs += 1
            automation.failed_runs += 1
            db.commit()
        
        raise
        
    finally:
        db.close()


@celery_app.task(name="app.tasks.automation_tasks.check_scheduled_automations")
def check_scheduled_automations():
    """
    Check for scheduled automations that need to run
    
    Runs every minute via Celery Beat
    """
    db = SessionLocal()
    
    try:
        now = datetime.utcnow()
        
        # Find automations that should run
        automations = db.query(Automation).filter(
            Automation.status == AutomationStatus.ACTIVE,
            Automation.trigger_type == "schedule",
            Automation.next_run_at <= now
        ).all()
        
        for automation in automations:
            # Trigger execution
            execute_automation.delay(
                str(automation.id),
                "schedule",
                {"scheduled_time": now.isoformat()}
            )
            
            # Update next run time (will be calculated by cron parser)
            from app.services.schedule_service import calculate_next_run
            automation.next_run_at = calculate_next_run(automation.schedule)
            db.commit()
        
        return f"Triggered {len(automations)} scheduled automations"
        
    finally:
        db.close()


@celery_app.task(name="app.tasks.automation_tasks.cleanup_old_runs")
def cleanup_old_runs(days_to_keep: int = 30):
    """
    Clean up old automation runs
    
    Args:
        days_to_keep: Number of days to keep runs (default: 30)
    
    Returns:
        Number of deleted runs
    """
    db = SessionLocal()
    
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        # Delete old completed runs
        deleted = db.query(AutomationRun).filter(
            AutomationRun.created_at < cutoff_date,
            AutomationRun.status.in_([RunStatus.SUCCESS, RunStatus.FAILED, RunStatus.CANCELLED])
        ).delete(synchronize_session=False)
        
        db.commit()
        
        return deleted
        
    finally:
        db.close()


@celery_app.task(base=BaseTask, bind=True, name="app.tasks.automation_tasks.cancel_automation_run")
def cancel_automation_run(self, run_id: str):
    """
    Cancel a running automation
    
    Args:
        run_id: Automation run UUID
    """
    db = SessionLocal()
    
    try:
        run = db.query(AutomationRun).filter(
            AutomationRun.id == UUID(run_id)
        ).first()
        
        if not run:
            raise ValueError(f"Run {run_id} not found")
        
        if not run.is_running:
            raise ValueError(f"Run {run_id} is not running")
        
        # Revoke Celery task
        if run.task_id:
            celery_app.control.revoke(run.task_id, terminate=True)
        
        # Update run status
        run.status = RunStatus.CANCELLED
        run.completed_at = datetime.utcnow()
        run.add_log("warning", "Automation run cancelled by user")
        
        db.commit()
        
        return f"Cancelled run {run_id}"
        
    finally:
        db.close()
