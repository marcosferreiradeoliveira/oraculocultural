import firebase_admin
from firebase_admin import credentials
import logging
import streamlit as st

_initialized = False

def initialize_firebase():
    global _initialized
    if not _initialized:
        try:
            if not firebase_admin._apps:
                if not hasattr(st, 'secrets'):
                    logging.error("st.secrets não está disponível. Verifique se está rodando no Streamlit Cloud.")
                    return False

                if "firebase_credentials" not in st.secrets:
                    logging.error("'firebase_credentials' não encontrado em st.secrets. Verifique as configurações no Streamlit Cloud.")
                    return False

                firebase_config_dict = st.secrets["firebase_credentials"]
                if not isinstance(firebase_config_dict, dict) or not firebase_config_dict.get("type") == "service_account":
                    logging.error("'firebase_credentials' em st.secrets não é um dicionário de conta de serviço válido.")
                    return False

                cred = credentials.Certificate(firebase_config_dict)
                firebase_admin.initialize_app(cred)
            _initialized = True
            return True
        except Exception as e:
            logging.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True