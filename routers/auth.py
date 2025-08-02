"""Authentication utilities for API routes."""

import logging
from fastapi import HTTPException, status, Header
from typing import Optional
from config import settings
from utils.openai_errors import authentication_error

logger = logging.getLogger(__name__)


async def verify_api_key(authorization: Optional[str] = Header(None)) -> str:
    """Verify API key from Authorization header - OpenAI API compatible."""
    logger.info(f"Authorization header received: {authorization[:20] if authorization else 'None'}...")
    logger.info(f"Expected API key: {settings.api_key[:20] if settings.api_key else 'None'}...")

    if not authorization:
        raise authentication_error("You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY)")

    if not authorization.startswith("Bearer "):
        raise authentication_error("Invalid authorization header format. Expected 'Bearer <api_key>'")

    token = authorization[7:]  # Remove "Bearer " prefix
    logger.info(f"Extracted token: {token[:20] if token else 'None'}...")

    if not token:
        raise authentication_error("API key cannot be empty")

    if settings.api_key and token != settings.api_key:
        logger.warning(f"API key mismatch. Received: {token[:20]}..., Expected: {settings.api_key[:20]}...")
        raise authentication_error("Incorrect API key provided")

    return token
