import logging
import streamlit as st

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# # Error Handling
class AppError(Exception):
    """Base exception class for application errors"""

    pass


def handle_error(error: Exception, context: str = None) -> None:
    """Centralized error handling with logging"""
    error_msg = f"Error in {context}: {str(error)}" if context else str(error)
    logger.error(error_msg, exc_info=True)
    st.error(error_msg)
