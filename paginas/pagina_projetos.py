import streamlit as st
import firebase_admin
from firebase_admin import firestore
import traceback
import time
from components import welcome_popup
from constants import USER_SESSION_KEY

def pagina_projetos():
    st.title("📋 Projetos")

    if not firebase_admin._apps:
        pass
    db = firestore.client()

    # Get user data from session state
    user_data = st.session_state.get(USER_SESSION_KEY)
    if user_data and 'uid' in user_data:
        user_id = user_data['uid']
        
        # Check if user has seen the welcome popup
        user_doc = db.collection('users').document(user_id).get()
        
        if not user_doc.exists or not user_doc.get('has_seen_welcome'):
            # Show welcome popup
            welcome_popup()
            # Mark that user has seen the welcome popup
            db.collection('users').document(user_id).set({
                'has_seen_welcome': True
            }, merge=True)

    # Tabs para Projetos e Editais
    tab1, tab2 = st.tabs(["📝 Projetos", "📄 Editais"])

    with tab1:
        # Código existente para listar projetos
        pass

    with tab2:
        st.subheader("Editais Disponíveis")
        
        # Botão para adicionar novo edital
        if st.button("📥 Adicionar Novo Edital", use_container_width=True):
            st.session_state['pagina_atual'] = 'cadastro_edital'
            st.rerun()
        
        st.markdown("---")
        
        # Busca editais no Firestore
        try:
            editais_ref = db.collection('editais').order_by('data_upload', direction=firestore.Query.DESCENDING)
            editais = editais_ref.get()
            
            if not editais:
                st.info("Nenhum edital cadastrado ainda.")
            else:
                for edital in editais:
                    edital_data = edital.to_dict()
                    with st.expander(f"📄 {edital_data.get('nome', 'Edital sem nome')}", expanded=True):
                        # Informações do edital
                        st.write("**Data de Inscrição:**")
                        st.write(edital_data.get('data_inscricao', 'Não definida'))
                        
                        st.write("**Categorias de Projetos:**")
                        for cat in edital_data.get('categorias', []):
                            st.write(f"- {cat}")
                        
                        st.write("**Textos Requeridos:**")
                        for texto in edital_data.get('textos_requeridos', []):
                            st.write(f"- {texto}")
                        
                        st.write("**Documentos Requeridos:**")
                        for doc in edital_data.get('documentos_requeridos', []):
                            st.write(f"- {doc}")
                        
                        # Botões de ação em uma linha separada
                        st.markdown("---")
                        if st.button("✏️ Editar Edital", key=f"edit_{edital.id}", use_container_width=True):
                            st.session_state['edital_para_editar'] = edital.id
                            st.session_state['pagina_atual'] = 'editar_edital'
                            st.rerun()
        
        except Exception as e:
            st.error(f"Erro ao carregar editais: {str(e)}")
            st.code(traceback.format_exc())

    # Botão para adicionar novo projeto
    if st.button("📝 Novo Projeto", use_container_width=True):
        st.session_state['pagina_atual'] = 'cadastro_projeto'
        st.rerun() 