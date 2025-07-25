"""OpenAI API compatible error handling utilities."""

from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from enum import Enum


class OpenAIErrorType(str, Enum):
    """OpenAI API error types."""
    INVALID_REQUEST_ERROR = "invalid_request_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_ERROR = "permission_error"
    NOT_FOUND_ERROR = "not_found_error"
    RATE_LIMIT_ERROR = "rate_limit_error"
    API_ERROR = "api_error"
    OVERLOADED_ERROR = "overloaded_error"


class OpenAIErrorCode(str, Enum):
    """OpenAI API error codes."""
    # Authentication errors
    INVALID_API_KEY = "invalid_api_key"
    MISSING_API_KEY = "missing_api_key"
    
    # Request errors
    INVALID_REQUEST = "invalid_request"
    INVALID_INPUT = "invalid_input"
    INVALID_MODEL = "invalid_model"
    MODEL_NOT_FOUND = "model_not_found"
    CONTEXT_LENGTH_EXCEEDED = "context_length_exceeded"
    BATCH_SIZE_EXCEEDED = "batch_size_exceeded"
    
    # Rate limit errors
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"
    
    # Server errors
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    OVERLOADED = "overloaded"


def create_openai_error(
    message: str,
    error_type: OpenAIErrorType,
    error_code: OpenAIErrorCode,
    param: Optional[str] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST
) -> HTTPException:
    """
    Create an OpenAI API compatible HTTPException.
    
    Args:
        message: Human-readable error message
        error_type: Type of error (from OpenAIErrorType enum)
        error_code: Specific error code (from OpenAIErrorCode enum)
        param: Parameter that caused the error (optional)
        status_code: HTTP status code
        
    Returns:
        HTTPException with OpenAI compatible error format
    """
    error_detail = {
        "error": {
            "message": message,
            "type": error_type.value,
            "code": error_code.value
        }
    }
    
    if param:
        error_detail["error"]["param"] = param
    
    return HTTPException(status_code=status_code, detail=error_detail)


def invalid_request_error(message: str, param: Optional[str] = None) -> HTTPException:
    """Create an invalid request error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.INVALID_REQUEST_ERROR,
        error_code=OpenAIErrorCode.INVALID_REQUEST,
        param=param,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def invalid_input_error(message: str, param: str = "input") -> HTTPException:
    """Create an invalid input error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.INVALID_REQUEST_ERROR,
        error_code=OpenAIErrorCode.INVALID_INPUT,
        param=param,
        status_code=status.HTTP_400_BAD_REQUEST
    )


def model_not_found_error(model_name: str) -> HTTPException:
    """Create a model not found error."""
    return create_openai_error(
        message=f"The model '{model_name}' does not exist",
        error_type=OpenAIErrorType.INVALID_REQUEST_ERROR,
        error_code=OpenAIErrorCode.MODEL_NOT_FOUND,
        param="model",
        status_code=status.HTTP_404_NOT_FOUND
    )


def context_length_exceeded_error(max_tokens: int, actual_tokens: int) -> HTTPException:
    """Create a context length exceeded error."""
    return create_openai_error(
        message=f"This model's maximum context length is {max_tokens} tokens. "
                f"However, you requested {actual_tokens} tokens.",
        error_type=OpenAIErrorType.INVALID_REQUEST_ERROR,
        error_code=OpenAIErrorCode.CONTEXT_LENGTH_EXCEEDED,
        param="input",
        status_code=status.HTTP_400_BAD_REQUEST
    )


def batch_size_exceeded_error(max_batch_size: int, actual_batch_size: int) -> HTTPException:
    """Create a batch size exceeded error."""
    return create_openai_error(
        message=f"Batch size cannot exceed {max_batch_size}. "
                f"You provided {actual_batch_size} inputs.",
        error_type=OpenAIErrorType.INVALID_REQUEST_ERROR,
        error_code=OpenAIErrorCode.BATCH_SIZE_EXCEEDED,
        param="input",
        status_code=status.HTTP_400_BAD_REQUEST
    )


def authentication_error(message: str = "Invalid API key provided") -> HTTPException:
    """Create an authentication error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.AUTHENTICATION_ERROR,
        error_code=OpenAIErrorCode.INVALID_API_KEY,
        status_code=status.HTTP_401_UNAUTHORIZED
    )


def rate_limit_error(message: str = "Rate limit exceeded") -> HTTPException:
    """Create a rate limit error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.RATE_LIMIT_ERROR,
        error_code=OpenAIErrorCode.RATE_LIMIT_EXCEEDED,
        status_code=status.HTTP_429_TOO_MANY_REQUESTS
    )


def internal_server_error(message: str = "Internal server error") -> HTTPException:
    """Create an internal server error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.API_ERROR,
        error_code=OpenAIErrorCode.INTERNAL_ERROR,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


def service_unavailable_error(message: str = "Service temporarily unavailable") -> HTTPException:
    """Create a service unavailable error."""
    return create_openai_error(
        message=message,
        error_type=OpenAIErrorType.OVERLOADED_ERROR,
        error_code=OpenAIErrorCode.SERVICE_UNAVAILABLE,
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE
    )


def handle_validation_error(validation_error: Exception) -> HTTPException:
    """
    Convert Pydantic validation errors to OpenAI compatible format.
    
    Args:
        validation_error: Pydantic ValidationError
        
    Returns:
        HTTPException with OpenAI compatible error format
    """
    error_message = str(validation_error)
    
    # Extract parameter name if possible
    param = None
    if hasattr(validation_error, 'errors'):
        errors = validation_error.errors()
        if errors and len(errors) > 0:
            first_error = errors[0]
            if 'loc' in first_error and first_error['loc']:
                param = first_error['loc'][-1]  # Get the last location element
    
    return invalid_input_error(error_message, param)


def handle_generic_error(error: Exception, context: str = "processing request") -> HTTPException:
    """
    Handle generic exceptions and convert to OpenAI compatible format.
    
    Args:
        error: The exception that occurred
        context: Context description for the error
        
    Returns:
        HTTPException with OpenAI compatible error format
    """
    error_message = f"An error occurred while {context}: {str(error)}"
    return internal_server_error(error_message)
