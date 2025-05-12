import streamlit as st
from firebase_admin import firestore

def get_user_projects(user_id):
    try:
        db = firestore.client()
        projetos_ref = db.collection('projetos').where('user_id', '==', user_id)
        projetos = projetos_ref.stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in projetos]
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []
