"""
API Exception Handlers
Custom exception handlers for better error responses
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle validation errors with user-friendly messages
    """
    errors = []
    for error in exc.errors():
        field = " -> ".join(str(loc) for loc in error["loc"])
        message = error["msg"]
        errors.append(f"{field}: {message}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": errors
        }
    )


async def integrity_error_handler(request: Request, exc: IntegrityError):
    """
    Handle database integrity errors
    """
    error_message = str(exc.orig) if hasattr(exc, 'orig') else str(exc)
    
    # Check for common integrity violations
    if "unique constraint" in error_message.lower():
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Resource already exists",
                "message": "A record with this information already exists"
            }
        )
    
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "detail": "Database integrity error",
            "message": "The operation could not be completed due to data constraints"
        }
    )


async def sqlalchemy_error_handler(request: Request, exc: SQLAlchemyError):
    """
    Handle general SQLAlchemy errors
    """
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Database error",
            "message": "An error occurred while processing your request"
        }
    )
