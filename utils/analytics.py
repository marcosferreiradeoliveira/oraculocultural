import streamlit as st

def track_event(event_name, event_params=None):
    """
    Rastreia um evento no Google Analytics.
    
    Args:
        event_name (str): Nome do evento a ser rastreado
        event_params (dict, optional): Parâmetros adicionais do evento
    """
    if event_params is None:
        event_params = {}
    
    # Adiciona informações do usuário se disponíveis
    if 'user' in st.session_state:
        event_params['user_id'] = st.session_state['user'].get('uid', 'anonymous')
    
    # Cria o script para rastrear o evento
    script = f"""
        <script>
            gtag('event', '{event_name}', {event_params});
        </script>
    """
    
    # Renderiza o script
    st.markdown(script, unsafe_allow_html=True)

def track_page_view(page_name):
    """
    Rastreia uma visualização de página no Google Analytics.
    
    Args:
        page_name (str): Nome da página sendo visualizada
    """
    script = f"""
        <script>
            gtag('event', 'page_view', {{
                'page_title': '{page_name}',
                'page_location': window.location.href,
                'page_path': window.location.pathname
            }});
        </script>
    """
    
    st.markdown(script, unsafe_allow_html=True) 