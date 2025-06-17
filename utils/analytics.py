import streamlit as st
from constants import USER_SESSION_KEY
import json
import datetime

def track_event(event_name, params=None):
    """
    Track an event in Google Analytics.
    
    Args:
        event_name (str): Name of the event to track
        params (dict, optional): Additional parameters for the event
    """
    if params is None:
        params = {}
    
    # Add user information if available
    if USER_SESSION_KEY in st.session_state and st.session_state[USER_SESSION_KEY] is not None:
        user_info = st.session_state[USER_SESSION_KEY]
        if isinstance(user_info, dict):
            params['user_id'] = user_info.get('uid', 'anonymous')
            params['user_email'] = user_info.get('email', 'anonymous')
    
    # Construct the gtag event
    script = f"""
    <script>
        gtag('event', '{event_name}', {params});
    </script>
    """
    
    # Render the script
    st.markdown(script, unsafe_allow_html=True)

def track_page_view(page_title, location=None, path=None):
    """
    Track a page view in Google Analytics.
    
    Args:
        page_title (str): Title of the page
        location (str, optional): Full URL of the page
        path (str, optional): Path portion of the URL
    """
    params = {
        'page_title': page_title
    }
    
    if location:
        params['page_location'] = location
    if path:
        params['page_path'] = path
    
    # Add user information if available
    if USER_SESSION_KEY in st.session_state and st.session_state[USER_SESSION_KEY] is not None:
        user_info = st.session_state[USER_SESSION_KEY]
        if isinstance(user_info, dict):
            params['user_id'] = user_info.get('uid', 'anonymous')
            params['user_email'] = user_info.get('email', 'anonymous')
    
    # Construct the gtag pageview
    script = f"""
    <script>
        gtag('event', 'page_view', {params});
    </script>
    """
    
    # Render the script
    st.markdown(script, unsafe_allow_html=True)

def init_analytics():
    """Inicializa o Google Analytics"""
    st.markdown("""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-Z5YJBVKP9B"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){dataLayer.push(arguments);}
        gtag('js', new Date());
        gtag('config', 'G-Z5YJBVKP9B');
    </script>
    """, unsafe_allow_html=True)

def log_analytics_event(event_name, event_params=None):
    """Log analytics events for debugging"""
    if not event_params:
        event_params = {}
    
    # Remove valores None do dicionário
    safe_params = {k: v for k, v in event_params.items() if v is not None}
    
    # Adiciona timestamp se não existir
    if 'timestamp' not in safe_params:
        safe_params['timestamp'] = datetime.datetime.now().isoformat()
    
    # Envia o evento via JavaScript
    st.components.v1.html(f"""
    <script>
        if (typeof gtag === 'function') {{
            gtag('event', '{event_name}', {json.dumps(safe_params)});
            console.log('Analytics Event:', '{event_name}', {json.dumps(safe_params)});
        }}
    </script>
    """, height=0) 