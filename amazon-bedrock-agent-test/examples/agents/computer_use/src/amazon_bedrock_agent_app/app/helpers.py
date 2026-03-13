from typing import Optional
import logging

import streamlit as st

from error import handle_error

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@st.cache_resource
def get_boto3_session():
    """Cache boto3 session"""
    import boto3

    return boto3.Session()


def validate_auth() -> Optional[str]:
    """Validate authentication with error handling"""
    try:

        session = get_boto3_session()
        if not session.get_credentials():
            return "You must have AWS credentials set up to use the Bedrock API."
        return None
    except Exception as e:
        handle_error(e, "validating authentication")
        return str(e)
