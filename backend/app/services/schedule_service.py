"""
Schedule Service

Helper service for cron schedule parsing and next run calculation

TASK-329: Create cron schedule parser
TASK-330: Add automation to scheduler
TASK-331: Create schedule validation
TASK-332: Add timezone support
TASK-333: Create schedule testing utility
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from croniter import croniter
from cron_descriptor import get_description
import pytz


def calculate_next_run(
    cron_expression: str, 
    base_time: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> datetime:
    """
    Calculate next run time from cron expression
    
    TASK-329: Cron schedule parser
    TASK-332: Timezone support
    
    Args:
        cron_expression: Cron format string (e.g., "0 9 * * MON-FRI")
        base_time: Base time for calculation (default: now)
        timezone: Timezone name (e.g., "America/New_York", "UTC")
    
    Returns:
        Next run datetime (UTC)
    
    Examples:
        "0 9 * * *" - Every day at 9 AM
        "0 9 * * MON-FRI" - Weekdays at 9 AM
        "*/15 * * * *" - Every 15 minutes
        "0 0 1 * *" - First day of every month at midnight
    """
    if not cron_expression:
        raise ValueError("Cron expression is required")
    
    # Handle timezone
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            if base_time is None:
                base_time = datetime.now(tz)
            elif base_time.tzinfo is None:
                # Localize naive datetime
                base_time = tz.localize(base_time)
            else:
                # Convert to target timezone
                base_time = base_time.astimezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")
    else:
        if base_time is None:
            base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        next_run = cron.get_next(datetime)
        
        # Convert to UTC for storage
        if next_run.tzinfo is not None:
            next_run = next_run.astimezone(pytz.UTC).replace(tzinfo=None)
        
        return next_run
    except Exception as e:
        raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")


def validate_cron_expression(cron_expression: str) -> bool:
    """
    Validate cron expression
    
    TASK-331: Schedule validation
    
    Args:
        cron_expression: Cron format string
    
    Returns:
        True if valid, False otherwise
    """
    if not cron_expression or not isinstance(cron_expression, str):
        return False
    
    try:
        # Check if croniter can parse it
        croniter(cron_expression)
        return True
    except Exception:
        return False


def get_schedule_description(cron_expression: str) -> str:
    """
    Get human-readable description of cron schedule
    
    TASK-331: Schedule validation
    
    Args:
        cron_expression: Cron format string
    
    Returns:
        Human-readable description
    
    Examples:
        "0 9 * * *" -> "At 09:00 AM"
        "*/15 * * * *" -> "Every 15 minutes"
    """
    try:
        return get_description(cron_expression)
    except Exception as e:
        return f"Invalid: {e}"


def calculate_next_n_runs(
    cron_expression: str,
    n: int = 5,
    base_time: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> List[datetime]:
    """
    Calculate next N run times
    
    TASK-333: Schedule testing utility
    
    Args:
        cron_expression: Cron format string
        n: Number of runs to calculate
        base_time: Base time for calculation
        timezone: Timezone name
    
    Returns:
        List of next N run times (UTC)
    """
    if not cron_expression:
        raise ValueError("Cron expression is required")
    
    if n <= 0:
        raise ValueError("n must be positive")
    
    # Handle timezone
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            if base_time is None:
                base_time = datetime.now(tz)
            elif base_time.tzinfo is None:
                base_time = tz.localize(base_time)
            else:
                base_time = base_time.astimezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")
    else:
        if base_time is None:
            base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        runs = []
        
        for _ in range(n):
            next_run = cron.get_next(datetime)
            # Convert to UTC
            if next_run.tzinfo is not None:
                next_run = next_run.astimezone(pytz.UTC).replace(tzinfo=None)
            runs.append(next_run)
        
        return runs
    except Exception as e:
        raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")


def test_schedule(
    cron_expression: str,
    timezone: Optional[str] = None,
    test_count: int = 5
) -> Dict[str, Any]:
    """
    Test a cron schedule and return detailed information
    
    TASK-333: Schedule testing utility
    
    Args:
        cron_expression: Cron format string
        timezone: Timezone name
        test_count: Number of next runs to calculate
    
    Returns:
        Dictionary with schedule test results
    """
    result = {
        "valid": False,
        "expression": cron_expression,
        "timezone": timezone or "UTC",
        "description": None,
        "next_runs": [],
        "error": None
    }
    
    # Validate
    if not validate_cron_expression(cron_expression):
        result["error"] = "Invalid cron expression"
        return result
    
    result["valid"] = True
    
    # Get description
    try:
        result["description"] = get_schedule_description(cron_expression)
    except Exception as e:
        result["description"] = f"Unable to describe: {e}"
    
    # Calculate next runs
    try:
        next_runs = calculate_next_n_runs(
            cron_expression, 
            n=test_count, 
            timezone=timezone
        )
        result["next_runs"] = [run.isoformat() for run in next_runs]
    except Exception as e:
        result["error"] = f"Error calculating next runs: {e}"
    
    return result


def get_supported_timezones() -> List[str]:
    """
    Get list of supported timezone names
    
    TASK-332: Timezone support
    
    Returns:
        List of timezone names
    """
    return pytz.all_timezones


def validate_timezone(timezone: str) -> bool:
    """
    Validate timezone name
    
    TASK-332: Timezone support
    
    Args:
        timezone: Timezone name
    
    Returns:
        True if valid, False otherwise
    """
    return timezone in pytz.all_timezones


def get_cron_description(cron_expression: str) -> str:
    """
    Get human-readable description of cron expression
    
    Args:
        cron_expression: Cron format string
    
    Returns:
        Human-readable description
    """
    try:
        return get_description(cron_expression)
    except Exception:
        return "Custom schedule"


def calculate_previous_run(cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculate previous run time from cron expression
    
    Args:
        cron_expression: Cron format string
        base_time: Base time for calculation (default: now)
    
    Returns:
        Previous run datetime
    """
    if not cron_expression:
        raise ValueError("Cron expression is required")
    
    if base_time is None:
        base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        return cron.get_prev(datetime)
    except Exception as e:
        raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")


# Common cron patterns
CRON_PATTERNS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "every_hour": "0 * * * *",
    "every_day_9am": "0 9 * * *",
    "every_day_midnight": "0 0 * * *",
    "weekdays_9am": "0 9 * * MON-FRI",
    "weekdays_5pm": "0 17 * * MON-FRI",
    "mondays_9am": "0 9 * * MON",
    "first_of_month": "0 0 1 * *",
    "last_day_of_month": "0 0 L * *",
}


__all__ = [
    "calculate_next_run",
    "calculate_previous_run",
    "validate_cron_expression",
    "get_cron_description",
    "test_schedule",
    "calculate_next_n_runs",
    "get_schedule_description",
    "get_supported_timezones",
    "validate_timezone",
    "CRON_PATTERNS"
]



def get_schedule_description(cron_expression: str) -> str:
    """
    Get human-readable description of cron schedule
    
    TASK-331: Schedule validation
    
    Args:
        cron_expression: Cron format string
    
    Returns:
        Human-readable description
    
    Examples:
        "0 9 * * *" -> "At 09:00 AM"
        "*/15 * * * *" -> "Every 15 minutes"
    """
    try:
        return get_description(cron_expression)
    except Exception as e:
        return f"Invalid: {e}"


def calculate_next_n_runs(
    cron_expression: str,
    n: int = 5,
    base_time: Optional[datetime] = None,
    timezone: Optional[str] = None
) -> List[datetime]:
    """
    Calculate next N run times
    
    TASK-333: Schedule testing utility
    
    Args:
        cron_expression: Cron format string
        n: Number of runs to calculate
        base_time: Base time for calculation
        timezone: Timezone name
    
    Returns:
        List of next N run times (UTC)
    """
    if not cron_expression:
        raise ValueError("Cron expression is required")
    
    if n <= 0:
        raise ValueError("n must be positive")
    
    # Handle timezone
    if timezone:
        try:
            tz = pytz.timezone(timezone)
            if base_time is None:
                base_time = datetime.now(tz)
            elif base_time.tzinfo is None:
                base_time = tz.localize(base_time)
            else:
                base_time = base_time.astimezone(tz)
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")
    else:
        if base_time is None:
            base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        runs = []
        
        for _ in range(n):
            next_run = cron.get_next(datetime)
            # Convert to UTC
            if next_run.tzinfo is not None:
                next_run = next_run.astimezone(pytz.UTC).replace(tzinfo=None)
            runs.append(next_run)
        
        return runs
    except Exception as e:
        raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")


def test_schedule(
    cron_expression: str,
    timezone: Optional[str] = None,
    test_count: int = 5
) -> Dict[str, Any]:
    """
    Test a cron schedule and return detailed information
    
    TASK-333: Schedule testing utility
    
    Args:
        cron_expression: Cron format string
        timezone: Timezone name
        test_count: Number of next runs to calculate
    
    Returns:
        Dictionary with schedule test results
    """
    result = {
        "valid": False,
        "expression": cron_expression,
        "timezone": timezone or "UTC",
        "description": None,
        "next_runs": [],
        "error": None
    }
    
    # Validate
    if not validate_cron_expression(cron_expression):
        result["error"] = "Invalid cron expression"
        return result
    
    result["valid"] = True
    
    # Get description
    try:
        result["description"] = get_schedule_description(cron_expression)
    except Exception as e:
        result["description"] = f"Unable to describe: {e}"
    
    # Calculate next runs
    try:
        next_runs = calculate_next_n_runs(
            cron_expression, 
            n=test_count, 
            timezone=timezone
        )
        result["next_runs"] = [run.isoformat() for run in next_runs]
    except Exception as e:
        result["error"] = f"Error calculating next runs: {e}"
    
    return result


def get_supported_timezones() -> List[str]:
    """
    Get list of supported timezone names
    
    TASK-332: Timezone support
    
    Returns:
        List of timezone names
    """
    return pytz.all_timezones


def validate_timezone(timezone: str) -> bool:
    """
    Validate timezone name
    
    TASK-332: Timezone support
    
    Args:
        timezone: Timezone name
    
    Returns:
        True if valid, False otherwise
    """
    return timezone in pytz.all_timezones


def get_cron_description(cron_expression: str) -> str:
    """
    Get human-readable description of cron expression
    
    Args:
        cron_expression: Cron format string
    
    Returns:
        Human-readable description
    """
    from cron_descriptor import get_description
    
    try:
        return get_description(cron_expression)
    except:
        return "Custom schedule"


def calculate_previous_run(cron_expression: str, base_time: Optional[datetime] = None) -> datetime:
    """
    Calculate previous run time from cron expression
    
    Args:
        cron_expression: Cron format string
        base_time: Base time for calculation (default: now)
    
    Returns:
        Previous run datetime
    """
    if not cron_expression:
        raise ValueError("Cron expression is required")
    
    if base_time is None:
        base_time = datetime.utcnow()
    
    try:
        cron = croniter(cron_expression, base_time)
        return cron.get_prev(datetime)
    except Exception as e:
        raise ValueError(f"Invalid cron expression '{cron_expression}': {e}")


# Common cron patterns
CRON_PATTERNS = {
    "every_minute": "* * * * *",
    "every_5_minutes": "*/5 * * * *",
    "every_15_minutes": "*/15 * * * *",
    "every_30_minutes": "*/30 * * * *",
    "every_hour": "0 * * * *",
    "every_day_9am": "0 9 * * *",
    "every_day_midnight": "0 0 * * *",
    "weekdays_9am": "0 9 * * MON-FRI",
    "weekdays_5pm": "0 17 * * MON-FRI",
    "mondays_9am": "0 9 * * MON",
    "first_of_month": "0 0 1 * *",
    "last_day_of_month": "0 0 L * *",
}


__all__ = [
    "calculate_next_run",
    "calculate_previous_run",
    "validate_cron_expression",
    "get_cron_description",
    "CRON_PATTERNS"
]
