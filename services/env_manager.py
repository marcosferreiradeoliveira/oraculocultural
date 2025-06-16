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
    print(f"DEBUG: Trying to get value for key_path: {key_path}")
    
    # First try to get from Streamlit secrets
    try:
        print("DEBUG: Checking Streamlit secrets...")
        print(f"DEBUG: Available secrets keys: {list(st.secrets.keys())}")
        
        keys = key_path.split(".")
        current = st.secrets
        for key in keys:
            print(f"DEBUG: Looking for key '{key}' in current dict: {list(current.keys()) if isinstance(current, dict) else 'not a dict'}")
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                print(f"DEBUG: Key '{key}' not found in current dict")
                break
        else:  # If we didn't break, we found the value
            print(f"DEBUG: Found value in Streamlit secrets: {current[:10]}..." if isinstance(current, str) else current)
            return current
    except Exception as e:
        print(f"DEBUG: Error accessing Streamlit secrets: {str(e)}")
        pass  # If any error occurs, continue to try environment variables

    # If not found in secrets, try environment variables
    print("DEBUG: Checking environment variables...")
    keys = key_path.split(".")
    env_dict = get_railway_env()
    
    current = env_dict
    for key in keys:
        print(f"DEBUG: Looking for key '{key}' in env_dict: {list(current.keys()) if isinstance(current, dict) else 'not a dict'}")
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            print(f"DEBUG: Key '{key}' not found in env_dict")
            return default
    
    print(f"DEBUG: Found value in env vars: {current[:10]}..." if isinstance(current, str) else current)
    return current 