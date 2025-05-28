import streamlit as st
from constants import USER_SESSION_KEY

# Google Analytics Measurement ID
GA_MEASUREMENT_ID = 'G-MBKVND6RMW'

def initialize_analytics():
    """
    Initialize Google Analytics with the correct Measurement ID.
    This should be called at the start of the app.
    """
    script = f"""
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
    <script>
        window.dataLayer = window.dataLayer || [];
        function gtag(){{dataLayer.push(arguments);}}
        gtag('js', new Date());
        gtag('config', '{GA_MEASUREMENT_ID}', {{
            'app_name': 'Oraculo Cultural',
            'app_version': '1.0',
            'stream_id': '11277564575',
            'stream_url': 'https://oraculocultural.streamlit.app/'
        }});
    </script>
    """
    st.markdown(script, unsafe_allow_html=True)

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
    
    # Add app information
    params.update({
        'app_name': 'Oraculo Cultural',
        'app_version': '1.0',
        'stream_id': '11277564575',
        'stream_url': 'https://oraculocultural.streamlit.app/'
    })
    
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
        'page_title': page_title,
        'app_name': 'Oraculo Cultural',
        'app_version': '1.0',
        'stream_id': '11277564575',
        'stream_url': 'https://oraculocultural.streamlit.app/'
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