import os
import json
from typing import Dict, Any, Optional
import streamlit as st

def get_railway_env() -> Dict[str, Any]:
    """
    Get environment variables from Railway.
    Returns a dictionary with all environment variables.
    """
    return {
        "openai": {
            "api_key": os.getenv("OPENAI_API_KEY")
        },
        "firebase_credentials": json.loads(os.getenv("FIREBASE_CREDENTIALS", "{}")),
        "mercadopago": {
            "access_token": os.getenv("MP_ACCESS_TOKEN"),
            "public_key": os.getenv("MP_PUBLIC_KEY"),
            "STREAMLIT_BASE_URL": os.getenv("STREAMLIT_BASE_URL")
        },
        "email": {
            "user": os.getenv("EMAIL_USER"),
            "password": os.getenv("EMAIL_PASSWORD")
        }
    }

def get_env_value(key_path: str, default: Any = None) -> Any:
    """
    Get a specific value from environment variables using a dot-notation path.
    First checks Streamlit secrets, then falls back to environment variables.
    Example: get_env_value("openai.api_key")
    """
    # First try to get from Streamlit secrets
    try:
        keys = key_path.split(".")
        current = st.secrets
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                break
        else:  # If we didn't break, we found the value
            return current
    except Exception:
        pass  # If any error occurs, continue to try environment variables

    # If not found in secrets, try environment variables
    keys = key_path.split(".")
    env_dict = get_railway_env()
    
    current = env_dict
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current 