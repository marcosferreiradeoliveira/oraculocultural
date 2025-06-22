import streamlit as st
import time
from services.firebase_init import initialize_firebase, get_error_message
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY
from utils.streamlit_analytics_helper import log_analytics_event

def pagina_novo_projeto():
    """Exibe a página de criação de novo projeto"""
    log_analytics_event('view_new_project_page')
    
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase_app()
    if not firebase_app:
        return

    st.header('✨ Criar Novo Projeto Cultural')
    
    @st.cache_data 
    def get_editais_cached():
        try:
            db = firestore.client()
            editais_ref = db.collection('editais').order_by('nome')
            editais_stream = editais_ref.stream()
            return [{'id': doc.id, **doc.to_dict()} for doc in editais_stream]
        except Exception as e:
            print(f"Erro ao recuperar editais (cache): {str(e)}")
            return []

    editais_disponiveis = get_editais_cached()
    if not editais_disponiveis and FIREBASE_APP_INITIALIZED: 
        st.info("Nenhum edital cadastrado no momento para associação.")

    edital_options = {'-- Selecione um Edital (Opcional) --': None}
    edital_options.update({edital['nome']: edital['id'] for edital in editais_disponiveis})

    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto*", help="O título principal do seu projeto.")
        descricao = st.text_area("Descrição Detalhada do Projeto*", height=150, help="Descreva os objetivos, público-alvo, e o que torna seu projeto único.")
        categoria = st.selectbox("Categoria Principal*", [
            "Artes Visuais", "Música", "Teatro", "Dança", 
            "Cinema e Audiovisual", "Literatura e Publicações", 
            "Patrimônio Cultural", "Artesanato", "Cultura Popular", "Outra"
        ], help="Selecione a categoria que melhor descreve seu projeto.")
        
        nome_edital_selecionado = st.selectbox(
            "Associar a um Edital (Opcional)",
            list(edital_options.keys()),
            help="Selecione um edital para associar este projeto."
        )
        submitted = st.form_submit_button("🚀 Salvar Projeto")
        
        if submitted:
            if not nome or not descricao or not categoria:
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
                log_analytics_event('project_creation_attempt', {'status': 'failed', 'reason': 'empty_fields'})
            else:
                try:
                    start_time = time.time()
                    db = firestore.client()
                    user_uid = st.session_state.get(USER_SESSION_KEY, {}).get('uid')
                    if not user_uid:
                        st.error("Erro: Usuário não identificado. Faça login novamente.")
                        log_analytics_event('project_creation_attempt', {'status': 'failed', 'reason': 'user_not_found'})
                        return

                    edital_id_selecionado = edital_options[nome_edital_selecionado]
                    novo_projeto_data = {
                        'nome': nome,
                        'descricao': descricao,
                        'categoria': categoria,
                        'user_id': user_uid,
                        'edital_associado': edital_id_selecionado,
                        'data_criacao': firestore.SERVER_TIMESTAMP,
                        'data_atualizacao': firestore.SERVER_TIMESTAMP,
                    }
                    db.collection('projetos').add(novo_projeto_data)
                    
                    end_time = time.time()
                    creation_time = end_time - start_time
                    
                    # Track successful project creation
                    log_analytics_event('project_creation_success', {
                        'project_name': nome,
                        'category': categoria,
                        'has_edital': bool(edital_id_selecionado),
                        'creation_time': creation_time
                    })
                    
                    st.success(f"Projeto '{nome}' criado com sucesso!")
                    st.balloons()
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                    st.rerun()
                except Exception as e:
                    log_analytics_event('project_creation_attempt', {
                        'status': 'failed',
                        'reason': 'error',
                        'error_message': str(e)
                    })
                    st.error(f"Erro ao salvar projeto: {str(e)}")
    
    if st.button("⬅️ Voltar para Projetos"):
        log_analytics_event('back_to_projects_click')
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun() 