import streamlit as st

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
    if 'user' in st.session_state:
        params['user_id'] = st.session_state['user'].get('uid', 'anonymous')
        params['user_email'] = st.session_state['user'].get('email', 'anonymous')
    
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
    if 'user' in st.session_state:
        params['user_id'] = st.session_state['user'].get('uid', 'anonymous')
        params['user_email'] = st.session_state['user'].get('email', 'anonymous')
    
    # Construct the gtag pageview
    script = f"""
    <script>
        gtag('event', 'page_view', {params});
    </script>
    """
    
    # Render the script
    st.markdown(script, unsafe_allow_html=True) 