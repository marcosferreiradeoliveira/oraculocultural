import streamlit as st
import os
from services.env_manager import get_env_value
from dotenv import load_dotenv # Importar load_dotenv
from firebase_admin import firestore # Adicionar importação do firestore
import json # Importado para tentar carregar JSON de string
import datetime # Para trabalhar com datas e horas
import streamlit.components.v1 as components

# Configuração da página - DEVE ser o primeiro comando Streamlit
st.set_page_config(
    page_title="Oráculo Cultural",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': "# Oráculo Cultural\nSua plataforma para decifrar o universo da cultura."
    }
)

def add_google_analytics():
    """
    Adiciona o script base do Google Analytics (gtag.js) ao cabeçalho da página.
    Este script é necessário para que a função `track_pageview` funcione.
    Ele é injetado de forma invisível no HTML.
    """
    ga_script = """
    <script async src="https://www.googletagmanager.com/gtag/js?id=G-Z5YJBVKP9B"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-Z5YJBVKP9B');
    </script>
    """
    components.html(ga_script, height=0)

# Adicione esta nova função junto com a anterior
def track_pageview(page_name):
    """
    Envia um evento de visualização de página (page_view) para o Google Analytics.
    Deve ser chamado toda vez que a página lógica da aplicação mudar.

    Argumentos:
        page_name (str): O nome da página para ser exibido no Google Analytics.
                         Ex: 'login', 'projetos', 'editar_projeto'.
    """
    tracking_script = f"""
    <script>
        gtag('event', 'page_view', {{
            page_title: '{page_name}',
            page_path: '/{page_name}'
        }});
    </script>
    """
    components.html(tracking_script, height=0)

st.markdown("""
    <style>
    .stAlert, .stNotification, .stException, .stWarning {
        display: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# Carregar variáveis de ambiente do arquivo .env (para desenvolvimento local)
load_dotenv()

# Debug: Verificar se o arquivo .env está sendo carregado
print("DEBUG: Verificando variáveis de ambiente...")
print(f"DEBUG: FIREBASE_CREDENTIALS presente: {'FIREBASE_CREDENTIALS' in os.environ}")
print(f"DEBUG: Conteúdo de FIREBASE_CREDENTIALS: {os.getenv('FIREBASE_CREDENTIALS')[:50]}..." if os.getenv('FIREBASE_CREDENTIALS') else "None")

# Configura as credenciais do Firebase
firebase_credentials = os.getenv('FIREBASE_CREDENTIALS')
if not firebase_credentials:
    st.error("""
    ⚠️ Credenciais do Firebase não encontradas!
    
    Por favor, certifique-se de que:
    1. O arquivo .env existe e contém a variável FIREBASE_CREDENTIALS
    2. A variável FIREBASE_CREDENTIALS contém um JSON válido com as credenciais do Firebase
    3. O arquivo .env está no diretório raiz do projeto
    
    Se estiver usando Railway, verifique se a variável de ambiente FIREBASE_CREDENTIALS está configurada corretamente.
    """)
    st.stop()
else:
    try:
        # Tenta validar o JSON antes de definir
        json.loads(firebase_credentials)
        os.environ['FIREBASE_CREDENTIALS'] = firebase_credentials
        print("DEBUG: Credenciais do Firebase carregadas com sucesso")
    except json.JSONDecodeError as e:
        st.error(f"""
        ⚠️ As credenciais do Firebase não são um JSON válido!
        
        Erro: {str(e)}
        
        Por favor, verifique se o conteúdo da variável a FIREBASE_CREDENTIALS é um JSON válido.
        """)
        st.stop()

# As importações necessárias devem vir após a configuração da página
from langchain_openai import ChatOpenAI
import datetime
import time
import firebase_admin
from google.api_core.datetime_helpers import DatetimeWithNanoseconds as GCloudTimestamp
import json
from streamlit.runtime.secrets import AttrDict
import traceback
from services.firebase_init import initialize_firebase, get_error_message

# Inicialização Centralizada do Firebase Admin
FIREBASE_APP_INITIALIZED = False 
FIREBASE_INIT_ERROR_MESSAGE = None


def initialize_firebase_app():
    global FIREBASE_APP_INITIALIZED, FIREBASE_INIT_ERROR_MESSAGE
    
    # Se já está inicializado, retorna True
    if FIREBASE_APP_INITIALIZED:
        return True
        
    success = initialize_firebase()
    FIREBASE_APP_INITIALIZED = success
    FIREBASE_INIT_ERROR_MESSAGE = get_error_message()
    return success

# Inicializa o Firebase antes de qualquer outra coisa
initialize_firebase_app()

# Configuração do OpenAI
llm = None
try:
    openai_api_key = get_env_value("openai.api_key")
    if not openai_api_key:
        print("AVISO: OpenAI API key não encontrada. Funcionalidades de IA podem ser limitadas.")
    else:
        llm = ChatOpenAI(
            openai_api_key=openai_api_key,
            model="gpt-3.5-turbo"
        )
        print("INFO: Cliente OpenAI inicializado com sucesso.")
except Exception as e:
    print(f"ERRO ao inicializar OpenAI: {str(e)}. Funcionalidades de IA podem ser limitadas.")
    llm = None

# Importações de modelos e utilitários
from models import (
    get_llm, 
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa
)
from loaders import carrega_pdf

# Importar constantes
from constants import (
    USER_SESSION_KEY,
    AUTENTICADO_SESSION_KEY,
    PAGINA_ATUAL_SESSION_KEY,
    PROJETO_SELECIONADO_KEY,
    TEXTO_PROJETO_KEY,
    RESUMO_KEY,
    ORCAMENTO_KEY,
    CRONOGRAMA_KEY,
    OBJETIVOS_KEY,
    JUSTIFICATIVA_KEY,
    EDITAL_SELECIONADO_KEY
)

# Importações de páginas (movidas para depois da inicialização do Firebase)
from paginas.login import pagina_login
try:
    from paginas.pagina_editar_projeto import pagina_editar_projeto as pagina_editar_projeto_view
except ImportError as e:
    st.error(f"Erro ao importar página de edição de projeto: {str(e)}")
    st.stop()
from paginas.reset_password import pagina_reset_password
from paginas.cadastro import pagina_cadastro
from paginas.pagina_perfil import pagina_perfil
from paginas.pagina_cadastro_edital import pagina_cadastro_edital
from paginas.pagina_pagamento_upgrade import pagina_pagamento_upgrade, pagina_payment_success, pagina_payment_failure, pagina_payment_pending
from paginas.pagina_cadastro_projeto import pagina_cadastro_projeto
from paginas.pagina_editar_edital import pagina_editar_edital
from paginas.pagina_assinatura import pagina_assinatura

# CSS customizado global
st.markdown("""
    <style>
        /* Esconder elementos padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Estilos gerais */
        .stApp {
            background-color: #F7F5F2;
        }
        
        /* Container principal */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
        }
        
        /* Títulos */
        h1, h2, h3 {
            color: #1e293b;
            font-weight: 600;
            margin-bottom: 1rem;
        }
        
        /* Cards de projeto */
        .project-card {
            background-color: white;
            border-radius: 12px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            border: 1px solid #e2e8f0;
            height: 220px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            border-color: #cbd5e1;
        }
        
        .project-card-content {
            flex-grow: 1;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .project-card h3 {
            color: #1e293b;
            font-size: 1.2rem;
            margin: 0 0 0.75rem 0;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        .project-card p {
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 0.75rem;
            line-height: 1.5;
        }
        
        .project-description {
            flex-grow: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            display: -webkit-box;
            -webkit-line-clamp: 2;
            -webkit-box-orient: vertical;
            margin-bottom: 1rem;
            max-height: 3em;
            line-height: 1.5;
            color: #64748b;
        }
        
        .project-card-actions {
            margin-top: auto;
            padding-top: 1rem;
            border-top: 1px solid #e2e8f0;
        }
        
        /* Botões */
        .stButton button {
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.2s ease;
        }
        
        .stButton button:hover {
            transform: translateY(-1px);
        }
        
        /* Specific styles for primary action buttons (pink) */
        .stButton button[kind="primary"] {
            background-color: #C02679 !important;
            color: white !important;
            border-color: #C02679 !important;
        }

        .stButton button[kind="primary"]:hover {
            background-color: #a01f61 !important;
            border-color: #a01f61 !important;
            color: white !important;
        }

        /* Specific styles for secondary action buttons (outlined) */
         .stButton button[kind="secondary"] {
            background-color: white !important;
            color: #C02679 !important;
            border: 1px solid #C02679 !important;
        }

        .stButton button[kind="secondary"]:hover {
            background-color: #f7f5f2 !important;
            color: #a01f61 !important;
            border-color: #a01f61 !important;
        }
        
        /* Containers de login e formulários */
        .login-container-direita {
            background-color: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border: 1px solid #e2e8f0;
        }
        
        /* Campos de entrada */
        .stTextInput input {
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        
        .stTextInput input:focus {
            border-color: #3b82f6;
            box-shadow: 0 0 0 1px #3b82f6;
        }
        
        /* Mensagens de sucesso e erro */
        .stSuccess {
            background-color: #f0fdf4;
            border: 1px solid #86efac;
            border-radius: 8px;
            padding: 1rem;
        }
        
        .stError {
            background-color: #fef2f2;
            border: 1px solid #fecaca;
            border-radius: 8px;
            padding: 1rem;
        }
        
        /* Responsividade */
        @media screen and (min-width: 1024px) {
            .main .block-container {
                max-width: 90%;
                padding-left: 5%;
                padding-right: 5%;
            }
        }
        
        /* Animações suaves */
        .stMarkdown, .stText, .stButton {
            animation: fadeIn 0.5s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Estilo para links */
        a {
            color: #3b82f6;
            text-decoration: none;
            transition: color 0.2s ease;
        }
        
        a:hover {
            color: #2563eb;
            text-decoration: underline;
        }
        
        /* Estilo para divisores */
        .stDivider {
            margin: 2rem 0;
            border-color: #e2e8f0;
        }
        
        /* Estilo para expanders */
        .streamlit-expanderHeader {
            background-color: #f8fafc;
            border-radius: 8px;
            border: 1px solid #e2e8f0;
        }
        
        /* Estilo para tooltips */
        .stTooltip {
            background-color: #1e293b;
            color: white;
            border-radius: 6px;
            padding: 0.5rem;
        }
        .top-menu {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            padding: 0.5rem 0;
            margin-bottom: 1rem;
            gap: 1rem;
        }
        .top-menu-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .top-menu-button {
            background: none;
            border: none;
            color: #64748b;
            font-size: 0.9rem;
            cursor: pointer;
            padding: 0;
            transition: color 0.2s ease;
        }
        .top-menu-button:hover {
            color: #C02679;
            text-decoration: underline;
        }
        .section-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1rem;
        }
        .section-header h2 {
            margin: 0;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .home-box {
            background-color: white;
            border-radius: 12px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
            border: 1px solid #e2e8f0;
            height: 250px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .home-box:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
            border-color: #cbd5e1;
        }
        .home-box h3 {
            color: #1e293b;
            font-size: 1.4rem;
            margin: 0 0 1rem 0;
        }
        .home-box p {
            color: #64748b;
            font-size: 1rem;
            line-height: 1.6;
            margin-bottom: 1.5rem;
        }
        .home-title {
            text-align: center;
            margin-bottom: 3rem;
        }
        .home-title h1 {
            font-size: 2.5rem;
            color: #1e293b;
            margin-bottom: 1rem;
        }
        .home-title h2 {
            font-size: 1.5rem;
            color: #475569;
            margin-bottom: 1rem;
        }
        .home-title p {
            font-size: 1.1rem;
            color: #64748b;
            max-width: 800px;
            margin: 0 auto;
        }

        /* Responsividade geral */
        @media (max-width: 992px) {
            .main .block-container {
                max-width: 100% !important;
                padding-left: 0.5rem !important;
                padding-right: 0.5rem !important;
            }
            .section-header, .top-menu {
                flex-direction: column !important;
                align-items: flex-start !important;
                gap: 0.5rem !important;
            }
            .project-card, .home-box {
                height: auto !important;
                min-height: 180px !important;
                padding: 1rem !important;
                margin-bottom: 1rem !important;
            }
            .project-card h3, .home-box h3 {
                font-size: 1rem !important;
            }
            .project-description {
                -webkit-line-clamp: 4 !important;
                max-height: 6em !important;
            }
            .stButton button {
                font-size: 1rem !important;
                padding: 0.5rem 1rem !important;
            }
            .stTextInput input {
                font-size: 1rem !important;
            }
            .stApp {
                padding: 0 !important;
            }
            .stMarkdown, .stText, .stButton {
                animation: none !important;
            }
            .stDivider {
                margin: 1rem 0 !important;
            }
            .stSuccess, .stError {
                padding: 0.5rem !important;
            }
        }
        @media (max-width: 600px) {
            .main .block-container {
                padding-left: 0.2rem !important;
                padding-right: 0.2rem !important;
            }
            .project-card, .home-box {
                padding: 0.5rem !important;
            }
            .project-card h3, .home-box h3 {
                font-size: 0.95rem !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

def get_user_projects(user_id):
    print(f"DEBUG get_user_projects: Verificando Firebase. Initialized={FIREBASE_APP_INITIALIZED}")
    if not FIREBASE_APP_INITIALIZED:
        st.error("Firebase não inicializado. Não é possível buscar projetos.")
        return []
    try:
        db = firestore.client()
        projetos_ref = db.collection('projetos').where('user_id', '==', user_id).order_by('data_criacao', direction=firestore.Query.DESCENDING)
        projetos_stream = projetos_ref.stream()
        projetos_lista = [{'id': doc.id, **doc.to_dict()} for doc in projetos_stream]
        return projetos_lista
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []

def pagina_projetos():
    """Página principal de projetos"""
    user_data = st.session_state.get(USER_SESSION_KEY)
    user_id = user_data.get('uid') if user_data else None
    
    print(f"DEBUG pagina_projetos: Verificando Firebase. Initialized={FIREBASE_APP_INITIALIZED}")
    if not FIREBASE_APP_INITIALIZED:
        st.error("ALERTA: A conexão com o banco de dados (Firebase) falhou. Funcionalidades limitadas.")
        return

    if not st.session_state.get(USER_SESSION_KEY):
        st.warning("Usuário não logado.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        # No need for rerun here, main will handle the redirect
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
    
    # Top menu bar
    st.markdown("""
    <style>
        .top-menu {
            display: flex;
            justify-content: flex-start;
            align-items: center;
            padding: 0.5rem 0;
            margin-bottom: 1rem;
            gap: 1rem;
        }
        .top-menu-content {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .top-menu-button {
            background: none;
            border: none;
            color: #64748b;
            font-size: 0.9rem;
            cursor: pointer;
            padding: 0;
            transition: color 0.2s ease;
        }
        .top-menu-button:hover {
            color: #C02679;
            text-decoration: underline;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Top menu with Profile and Logout
    st.markdown('<div class="top-menu">', unsafe_allow_html=True)
    
    # Create a single line with welcome message and buttons
    col1, col2, col3 = st.columns([3, 0.5, 0.5])
    
    with col1:
        st.markdown(f"<h3 style='margin: 0; font-size: 1.2rem;'>Bem-vindo(a), {display_name}</h3>", unsafe_allow_html=True)
    
    with col2:
        if st.button("Perfil", key="profile_button", use_container_width=True):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
            st.rerun()
    
    with col3:
        if st.button("Sair", key="logout_button", use_container_width=True):
            keys_to_clear = [
                USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PROJETO_SELECIONADO_KEY,
                TEXTO_PROJETO_KEY, RESUMO_KEY, ORCAMENTO_KEY, CRONOGRAMA_KEY,
                OBJETIVOS_KEY, JUSTIFICATIVA_KEY, EDITAL_SELECIONADO_KEY
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            project_specific_keys_patterns = [user_info.get('uid','temp_id_clear'), 'diagnostico_editavel', 'doc_gerado', 'projeto_para_excluir']
            keys_to_remove_session = [k for k in st.session_state if any(pattern in k for pattern in project_specific_keys_patterns)]
            for key in keys_to_remove_session:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.success("Você saiu da sua conta.")
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Projetos Section (First)
    st.markdown('<div class="section-header"><h2>🎨 Meus Projetos Culturais</h2>', unsafe_allow_html=True)
    if st.button("✨ Criar Novo Projeto", key="btn_novo_projeto", type="primary"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'novo_projeto'
        if PROJETO_SELECIONADO_KEY in st.session_state: del st.session_state[PROJETO_SELECIONADO_KEY]
        if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    projetos = get_user_projects(user_info['uid'])
    
    if not projetos:
        st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem; background-color: #e9ecef; border-radius: 10px; margin-top: 2rem;">
                <h3>Você ainda não tem projetos cadastrados.</h3>
                <p>Clique em "Criar Novo Projeto" para começar sua jornada cultural!</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        num_cols = 3
        cols = st.columns(num_cols)
        for i, projeto in enumerate(projetos):
            col_index = i % num_cols
            with cols[col_index]:
                card_html = f""" 
                <div class="project-card">
                    <div class="project-card-content">
                        <h3>{'📄' if projeto.get('edital_associado') else '🎵' if projeto.get('categoria') == 'Música' else '🖼️' if projeto.get('categoria') == 'Artes Visuais' else '🎭' if projeto.get('categoria') == 'Teatro' else '💃' if projeto.get('categoria') == 'Dança' else '🎬' if projeto.get('categoria') == 'Cinema e Audiovisual' else '📚' if projeto.get('categoria') == 'Literatura e Publicações' else '🏛️' if projeto.get('categoria') == 'Patrimônio Cultural' else '🧶' if projeto.get('categoria') == 'Artesanato' else '🥁' if projeto.get('categoria') == 'Cultura Popular' else '✨'} {projeto.get('nome', 'Projeto sem nome')}</h3>
                        <p style="color: #C02679; font-size: 0.9rem; margin: 0.2rem 0;">Categoria: {projeto.get('categoria', 'Não definida')}</p>
                        <p class="project-description">{projeto.get('descricao', 'Sem descrição')}</p>
                    </div>
                    <div class="project-card-actions">
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                btn_cols_card = st.columns(2)
                with btn_cols_card[0]:
                    if st.button(f"📝 Editar", key=f"editar_{projeto['id']}", type="secondary", use_container_width=True):
                        st.session_state[PROJETO_SELECIONADO_KEY] = projeto
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_projeto'
                        st.rerun()
                with btn_cols_card[1]:
                    if st.button(f"🗑️ Excluir", key=f"excluir_{projeto['id']}", type="secondary", use_container_width=True):
                        st.session_state['projeto_para_excluir'] = projeto
                        st.rerun()

    # Confirmação de exclusão de projeto
    if 'projeto_para_excluir' in st.session_state:
        projeto_para_excluir = st.session_state['projeto_para_excluir']
        st.warning(f"⚠️ Você está prestes a excluir o projeto '{projeto_para_excluir.get('nome', 'Sem nome')}'")
        st.write("Esta ação não pode ser desfeita.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirmar Exclusão", type="primary", use_container_width=True):
                try:
                    db = firestore.client()
                    db.collection('projetos').document(projeto_para_excluir['id']).delete()
                    st.success(f"Projeto '{projeto_para_excluir.get('nome', 'Sem nome')}' excluído com sucesso!")
                    del st.session_state['projeto_para_excluir']
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir projeto: {str(e)}")
        
        with col2:
            if st.button("❌ Cancelar", use_container_width=True):
                del st.session_state['projeto_para_excluir']
                st.rerun()

    st.markdown("---")
    
    # Editais Section (Moved below projects)
    st.markdown('<div class="section-header"><h2>📄 Editais Cadastrados</h2>', unsafe_allow_html=True)
    if st.button("📥 Cadastrar Novo Edital", key="btn_novo_edital", type="primary"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'cadastro_edital'
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # List editais
    try:
        db = firestore.client()
        editais_ref = db.collection('editais').order_by('nome')
        editais_stream = editais_ref.stream()
        editais_lista = [{'id': doc.id, **doc.to_dict()} for doc in editais_stream]
        
        if not editais_lista:
            st.info("Nenhum edital cadastrado no momento.")
        else:
            num_cols_editais = 3 # Number of columns for editais, same as projects
            cols_editais = st.columns(num_cols_editais)
            for i, edital in enumerate(editais_lista):
                col_index_editais = i % num_cols_editais
                with cols_editais[col_index_editais]:
                    # Card structure for each edital
                    card_html_edital = f""" 
                    <div class="project-card"> <!-- Using project-card class for similar styling -->
                        <div class="project-card-content">
                            <h3>📄 {edital.get('nome', 'Edital sem nome')}</h3>
                            <p style="font-size: 0.9rem; color: #334155; margin: 0;"><strong>Data de Inscrição:</strong> {edital.get('data_inscricao', 'Não definida')}</p>
                            <p style="font-size: 0.9rem; color: #334155; margin: 0.2rem 0;"><strong>Categorias de Projetos:</strong> {', '.join(edital.get('categorias', [])) if edital.get('categorias') else 'Não definidas'}</p>
                            <p style="font-size: 0.9rem; color: #334155; margin: 0.2rem 0;"><strong>Textos Requeridos:</strong> {', '.join(edital.get('textos_requeridos', [])) if edital.get('textos_requeridos') else 'Não definidos'}</p>
                            <p style="font-size: 0.9rem; color: #334155; margin: 0.2rem 0;"><strong>Documentos Requeridos:</strong> {', '.join(edital.get('documentos_requeridos', [])) if edital.get('documentos_requeridos') else 'Não definidos'}</p>
                        </div>
                        <div class="project-card-actions">
                        </div>
                    </div>
                    """
                    st.markdown(card_html_edital, unsafe_allow_html=True)
                    
                    btn_cols_card_edital = st.columns(2)
                    with btn_cols_card_edital[0]:
                        if st.button(f"📝 Editar", key=f"editar_edital_{edital['id']}", type="secondary", use_container_width=True):
                            st.session_state['edital_para_editar'] = edital['id']
                            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_edital'
                            st.rerun()
                    with btn_cols_card_edital[1]:
                        if st.button(f"🗑️ Excluir", key=f"excluir_edital_{edital['id']}", type="secondary", use_container_width=True):
                            st.session_state['edital_para_excluir'] = edital
                            st.rerun()

    except Exception as e:
        st.error(f"Erro ao carregar editais: {str(e)}")

    # Confirmação de exclusão de edital (Add this block)
    if 'edital_para_excluir' in st.session_state:
        edital_para_excluir = st.session_state['edital_para_excluir']
        st.warning(f"⚠️ Você está prestes a excluir o edital '{edital_para_excluir.get('nome', 'Sem nome')}'")
        st.write("Esta ação não pode ser desfeita.")
        
        col1_edital_del, col2_edital_del = st.columns(2)
        with col1_edital_del:
            if st.button("✅ Confirmar Exclusão", key="confirmar_exclusao_edital", type="primary", use_container_width=True):
                try:
                    db = firestore.client()
                    db.collection('editais').document(edital_para_excluir['id']).delete()
                    st.success(f"Edital '{edital_para_excluir.get('nome', 'Sem nome')}' excluído com sucesso!")
                    del st.session_state['edital_para_excluir']
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir edital: {str(e)}")
        
        with col2_edital_del:
            if st.button("❌ Cancelar", key="cancelar_exclusao_edital", use_container_width=True):
                del st.session_state['edital_para_excluir']
                st.rerun()

def pagina_novo_projeto():
    """Página de criação de novo projeto"""
    user_data = st.session_state.get(USER_SESSION_KEY)
    user_id = user_data.get('uid') if user_data else None
    
    print(f"DEBUG pagina_novo_projeto: Verificando Firebase. Initialized={FIREBASE_APP_INITIALIZED}")
    if not FIREBASE_APP_INITIALIZED:
        st.error("ALERTA: A conexão com o banco de dados (Firebase) falhou. Não é possível criar novo projeto.")
        if st.button("⬅️ Voltar para Login", key="novo_proj_voltar_login_err"): 
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
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
            else:
                try:
                    db = firestore.client()
                    user_uid = st.session_state.get(USER_SESSION_KEY, {}).get('uid')
                    if not user_uid:
                        st.error("Erro: Usuário não identificado. Faça login novamente.")
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
                    st.success(f"Projeto '{nome}' criado com sucesso!")
                    st.balloons()
                    
                    # Get the newly created project ID
                    projetos_ref = db.collection('projetos').where('user_id', '==', user_uid).order_by('data_criacao', direction=firestore.Query.DESCENDING).limit(1)
                    novo_projeto = next(projetos_ref.stream())
                    
                    # Set the project in session state and redirect to edit page
                    st.session_state[PROJETO_SELECIONADO_KEY] = {'id': novo_projeto.id, **novo_projeto.to_dict()}
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_projeto'
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {str(e)}")
    
    if st.button("⬅️ Voltar para Projetos"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun()

def main():
    """Função principal da aplicação"""
    print(f"DEBUG main(): Verificando FIREBASE_APP_INITIALIZED = {FIREBASE_APP_INITIALIZED}. Erro capturado: {FIREBASE_INIT_ERROR_MESSAGE}")
    # Verifica se o Firebase foi inicializado corretamente
    if not FIREBASE_APP_INITIALIZED:
        error_display_message = FIREBASE_INIT_ERROR_MESSAGE or "Erro desconhecido durante a inicialização do Firebase."
        st.error(f"Falha crítica na inicialização do Firebase. A aplicação não pode continuar. Detalhe: {error_display_message}")
        st.stop() 
    if llm is None and st.session_state.get(PAGINA_ATUAL_SESSION_KEY, 'login') not in ['login', 'cadastro', 'reset_password']:
        st.warning("O modelo de linguagem (OpenAI) não foi inicializado. Algumas funcionalidades podem estar indisponíveis ou apresentar erros.")
    if AUTENTICADO_SESSION_KEY not in st.session_state:
        st.session_state[AUTENTICADO_SESSION_KEY] = False
    if USER_SESSION_KEY not in st.session_state:
        st.session_state[USER_SESSION_KEY] = None
    if PAGINA_ATUAL_SESSION_KEY not in st.session_state:
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'cadastro'
    # Verificar se há um parâmetro 'page' na URL (vindo de redirects externos como Mercado Pago)
    query_params = st.experimental_get_query_params()
    if "page" in query_params:
        page_from_query_list = query_params.get("page")
        if page_from_query_list:
            page_from_query = page_from_query_list[0] # Pega o primeiro valor
            # Valide 'page_from_query' contra uma lista de páginas permitidas por query param
            allowed_query_pages = ['payment_success', 'payment_failure', 'payment_pending']
            if page_from_query in allowed_query_pages:
                st.session_state[PAGINA_ATUAL_SESSION_KEY] = page_from_query
                # Limpar os query_params para evitar re-roteamento em reruns internos
                st.experimental_set_query_params()
    # Verifica se o usuário está autenticado
    is_authenticated = st.session_state.get(AUTENTICADO_SESSION_KEY, False)
    current_page_on_entry = st.session_state[PAGINA_ATUAL_SESSION_KEY]
        track_pageview(current_page_on_entry)
 # Página que será renderizada por padrão
    # Se não estiver autenticado, mostra a página de login, cadastro ou reset de senha
    if not is_authenticated:
        if current_page_on_entry == 'cadastro':
            pagina_cadastro()
        elif current_page_on_entry == 'reset_password':
            pagina_reset_password()
        else:
            pagina_login()
        return
    else: # Usuário está autenticado
        # Lógica de redirecionamento pós-login
        if st.session_state.get('just_logged_in', False):
            del st.session_state['just_logged_in'] # Consome a flag
            final_target_page = 'editar_projeto'
            if current_page_on_entry != 'editar_projeto':
                st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_projeto'
                st.rerun(); return
        # Else, proceed with normal routing based on current_page
        # --- Routing for Authenticated Users (usa final_target_page) ---
        print(f"DEBUG: Página atual = {final_target_page}")
        if final_target_page == 'projetos':
            pagina_projetos()
        elif final_target_page == 'novo_projeto':
            pagina_novo_projeto()
        elif final_target_page == 'editar_projeto':
            pagina_editar_projeto_view() 
        elif final_target_page == 'pagamento_upgrade':
            pagina_pagamento_upgrade()
        elif final_target_page == 'payment_success':
            pagina_payment_success()
        elif final_target_page == 'payment_failure':
            pagina_payment_failure()
        elif final_target_page == 'payment_pending':
            pagina_payment_pending()
        elif final_target_page == 'perfil':
            pagina_perfil()
        elif final_target_page == 'cadastro_edital':
            pagina_cadastro_edital() 
        elif final_target_page == 'cadastro_projeto':
            pagina_cadastro_projeto()
        elif final_target_page == 'editar_edital':
            edital_id = st.session_state.get('edital_para_editar')
            if edital_id:
                pagina_editar_edital(edital_id)
            else:
                st.error("ID do edital não encontrado")
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()
        elif final_target_page == 'assinatura':
            pagina_assinatura()
        else:
            # Fallback for unknown authenticated page
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()

if __name__ == '__main__':
        add_google_analytics()

        main()
