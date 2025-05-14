import firebase_admin
from firebase_admin import credentials
import logging

_initialized = False

def initialize_firebase():
    global _initialized
    if not _initialized:
        try:
            if not firebase_admin._apps:
                cred = credentials.Certificate("config/firebase-service-account.json")
                firebase_admin.initialize_app(cred)
            _initialized = True
            return True
        except Exception as e:
            logging.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True