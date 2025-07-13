"""Authentication utilities for API routes."""

from fastapi import HTTPException, status, Header
from typing import Optional
from config import settings


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Verify API key from Authorization header."""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required"
        )
    
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must start with 'Bearer '"
        )
    
    token = authorization[7:]  # Remove "Bearer " prefix
    
    if settings.api_key and token != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key"
        )
    
    return token
