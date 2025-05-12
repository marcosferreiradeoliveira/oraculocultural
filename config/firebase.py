import streamlit as st
import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred = credentials.Certificate("config/firebase-service-account.json")
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True
