import streamlit as st
import firebase_admin
from firebase_admin import firestore
import traceback
import time
from components import welcome_popup
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message
from utils.streamlit_analytics_helper import log_analytics_event

def pagina_projetos():
    """Exibe a página de projetos com layout moderno e otimizado"""
    log_analytics_event('view_projects_page')
    
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase_app()
    if not firebase_app:
        return

    if not st.session_state.get(USER_SESSION_KEY):
        st.warning("Usuário não logado.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

    user_info = st.session_state[USER_SESSION_KEY]
    
    # Get user's full name from database
    try:
        db = firestore.client()
        user_doc = db.collection('usuarios').where('uid', '==', user_info['uid']).limit(1).get()
        user_data = next(user_doc, None)
        if user_data:
            user_data = user_data.to_dict()
            display_name = user_data.get('nome_completo', user_info.get('display_name', 'Usuário'))
        else:
            display_name = user_info.get('display_name', 'Usuário')
    except Exception as e:
        display_name = user_info.get('display_name', 'Usuário')

    # Projetos Section
    st.markdown('<div class="section-header"><h2>🎨 Meus Projetos Culturais</h2>', unsafe_allow_html=True)
    if st.button("✨ Criar Novo Projeto", key="btn_novo_projeto", type="primary"):
        log_analytics_event('create_project_click')
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'novo_projeto'
        if PROJETO_SELECIONADO_KEY in st.session_state: del st.session_state[PROJETO_SELECIONADO_KEY]
        if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

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