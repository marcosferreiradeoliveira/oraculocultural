import streamlit_analytics

def log_analytics_event(event_name, properties={}):
    try:
        args = []
        for key, value in properties.items():
            args.append(str(key))
            args.append(str(value))
        streamlit_analytics.log_event(event_name, *args)
    except Exception as e:
        print(f"DEBUG: Failed to log analytics event '{event_name}': {e}") 