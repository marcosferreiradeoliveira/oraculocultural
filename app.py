import streamlit as st

# Configuração da página Streamlit (deve ser a primeira chamada Streamlit NO SCRIPT PRINCIPAL)
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

import tempfile
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv # Para carregar variáveis de .env
import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1 import FieldFilter # Usado em get_user_projects
import json # Importado para tentar carregar JSON de string
from streamlit.runtime.secrets import AttrDict # Import AttrDict para verificação de tipo

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

# Importações de páginas
from paginas.login import pagina_login
from paginas.pagina_editar_projeto import pagina_editar_projeto as pagina_editar_projeto_view
from paginas.reset_password import pagina_reset_password
from paginas.cadastro import pagina_cadastro
from paginas.pagina_cadastro_edital import pagina_cadastro_edital

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

# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Configuração do OpenAI
llm = None 
try:
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if not openai_api_key and hasattr(st, 'secrets'): 
        openai_api_key = st.secrets.get("openai", {}).get("api_key")
        
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

# Inicialização Centralizada do Firebase Admin
FIREBASE_APP_INITIALIZED = False 
FIREBASE_INIT_ERROR_MESSAGE = None # Para armazenar a mensagem de erro da inicialização

def initialize_firebase_app():
    global FIREBASE_APP_INITIALIZED, FIREBASE_INIT_ERROR_MESSAGE
    if firebase_admin._apps: 
        FIREBASE_APP_INITIALIZED = True
        print("INFO: Firebase Admin já estava inicializado.")
        return True

    print("INFO: Tentando inicializar Firebase Admin...")
    try:
        if not hasattr(st, 'secrets'):
            error_msg = "ERRO CRÍTICO: st.secrets não está disponível. Impossível carregar credenciais no Streamlit Cloud."
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        if "firebase_credentials" not in st.secrets:
            error_msg = "ERRO CRÍTICO: 'firebase_credentials' não encontrado em st.secrets. Verifique as configurações no Streamlit Cloud."
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        # Get raw credentials and convert to dictionary
        raw_creds = st.secrets["firebase_credentials"]
        print(f"DEBUG: Tipo do raw_creds: {type(raw_creds)}")
        
        # Convert to dictionary
        if isinstance(raw_creds, AttrDict):
            print("DEBUG: Convertendo AttrDict para dicionário...")
            firebase_config_dict = {
                'type': str(raw_creds.type),
                'project_id': str(raw_creds.project_id),
                'private_key_id': str(raw_creds.private_key_id),
                'private_key': str(raw_creds.private_key),
                'client_email': str(raw_creds.client_email),
                'client_id': str(raw_creds.client_id),
                'auth_uri': str(raw_creds.auth_uri),
                'token_uri': str(raw_creds.token_uri),
                'auth_provider_x509_cert_url': str(raw_creds.auth_provider_x509_cert_url),
                'client_x509_cert_url': str(raw_creds.client_x509_cert_url),
                'universe_domain': str(raw_creds.universe_domain)
            }
        elif isinstance(raw_creds, dict):
            print("DEBUG: Usando dicionário diretamente...")
            firebase_config_dict = raw_creds
        else:
            error_msg = f"ERRO: Tipo de credencial não suportado: {type(raw_creds)}"
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        print("DEBUG: Verificando campos do dicionário...")
        print(f"DEBUG: Chaves disponíveis: {list(firebase_config_dict.keys())}")
        print(f"DEBUG: Tipo de credencial: {firebase_config_dict.get('type')}")
        print(f"DEBUG: Project ID: {firebase_config_dict.get('project_id')}")

        # Validate required fields
        required_fields = [
            'type', 'project_id', 'private_key_id', 'private_key',
            'client_email', 'client_id', 'auth_uri', 'token_uri',
            'auth_provider_x509_cert_url', 'client_x509_cert_url'
        ]

        missing_fields = [field for field in required_fields if field not in firebase_config_dict]
        if missing_fields:
            error_msg = f"ERRO: Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        if firebase_config_dict.get('type') != "service_account":
            error_msg = f"ERRO: Tipo de credencial inválido: {firebase_config_dict.get('type')}"
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        # Process private key
        private_key = firebase_config_dict.get('private_key', '')
        if not private_key:
            error_msg = "ERRO: Chave privada não encontrada"
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        # Clean up private key
        private_key = private_key.replace('\\n', '\n').strip()
        if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----'):
            error_msg = "ERRO: Formato inválido da chave privada"
            print(error_msg)
            FIREBASE_INIT_ERROR_MESSAGE = error_msg
            FIREBASE_APP_INITIALIZED = False
            return False

        # Update the private key in the config
        firebase_config_dict['private_key'] = private_key

        print("DEBUG: Tentando inicializar Firebase Admin com as credenciais...")
        cred = credentials.Certificate(firebase_config_dict)
        firebase_admin.initialize_app(cred)
        print("INFO: Firebase Admin inicializado com sucesso!")
        FIREBASE_APP_INITIALIZED = True
        return True

    except Exception as e:
        error_msg = f"ERRO ao inicializar Firebase Admin: {str(e)}"
        print(error_msg)
        print("DEBUG: Stack trace:", traceback.format_exc())
        FIREBASE_INIT_ERROR_MESSAGE = error_msg
        FIREBASE_APP_INITIALIZED = False
        return False

initialize_firebase_app()
print(f"DEBUG app.py global: FIREBASE_APP_INITIALIZED = {FIREBASE_APP_INITIALIZED}, Error: {FIREBASE_INIT_ERROR_MESSAGE}")


# CSS customizado global
st.markdown("""
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .project-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
            height: 220px; 
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .project-card h3 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: #333;
            font-size: 1.1rem; 
        }
        .project-card p {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: #555;
            flex-grow: 1; 
            overflow: hidden; 
            text-overflow: ellipsis; 
            display: -webkit-box;
            -webkit-line-clamp: 3; 
            -webkit-box-orient: vertical;
        }
        .project-card-actions {
            margin-top: auto; 
        }

        @media screen and (min-width: 1024px) {
            .main .block-container {
                max-width: 90%;
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
        projetos_ref = db.collection('projetos').where(filter=FieldFilter('user_id', '==', user_id)).order_by('data_criacao', direction=firestore.Query.DESCENDING)
        projetos_stream = projetos_ref.stream()
        projetos_lista = [{'id': doc.id, **doc.to_dict()} for doc in projetos_stream]
        return projetos_lista
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []

def pagina_projetos():
    print(f"DEBUG pagina_projetos: Verificando Firebase. Initialized={FIREBASE_APP_INITIALIZED}")
    if not FIREBASE_APP_INITIALIZED:
        st.error("ALERTA: A conexão com o banco de dados (Firebase) falhou. Funcionalidades limitadas.")
        return

    if not st.session_state.get(USER_SESSION_KEY):
        st.warning("Usuário não logado.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

    user_info = st.session_state[USER_SESSION_KEY]
    st.title(f'Bem-vindo(a), {user_info.get("display_name", user_info.get("email", "Usuário"))}!')
    
    if st.button("Sair", key="logout_button_projetos"):
        keys_to_clear = [
            USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PROJETO_SELECIONADO_KEY,
            TEXTO_PROJETO_KEY, RESUMO_KEY, ORCAMENTO_KEY, CRONOGRAMA_KEY,
            OBJETIVOS_KEY, JUSTIFICATIVA_KEY, EDITAL_SELECIONADO_KEY
        ]
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        project_specific_keys = [k for k in st.session_state if user_info.get('uid','temp_id_clear') in k or 'diagnostico_editavel' in k or 'doc_gerado' in k]
        for key in project_specific_keys:
            if key in st.session_state:
                del st.session_state[key]

        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.success("Você saiu da sua conta.")
        st.rerun()
    
    if 'ultimas_alteracoes' in st.session_state:
        alteracoes = st.session_state['ultimas_alteracoes']
        st.success(f"✅ Alterações aplicadas no projeto: {alteracoes.get('nome_projeto', 'N/A')}")
        with st.expander("📝 Ver detalhes das alterações"):
            st.markdown(alteracoes.get('alteracoes', 'Nenhuma descrição de alteração.'))
        del st.session_state['ultimas_alteracoes']

    projetos = get_user_projects(user_info['uid'])
    st.header('Meus Projetos Culturais', divider='rainbow')
    
    col_create1, col_create2 = st.columns(2)
    with col_create1:
        if st.button("🎨 Criar Novo Projeto", type="primary", use_container_width=True):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'novo_projeto'
            if PROJETO_SELECIONADO_KEY in st.session_state: del st.session_state[PROJETO_SELECIONADO_KEY]
            if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
            st.rerun()
    with col_create2:
        if st.button("📥 Cadastrar Novo Edital", type="secondary", use_container_width=True):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'cadastro_edital'
            st.rerun()

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
                    <div>
                        <h3>{projeto.get('nome', 'Projeto sem nome')}</h3>
                        <p><strong>Categoria:</strong> {projeto.get('categoria', 'Não definida')}</p>
                        <p>{projeto.get('descricao', 'Sem descrição')}</p>
                    </div>
                    <div class="project-card-actions">
                        {''}
                    </div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                btn_cols_card = st.columns(2)
                with btn_cols_card[0]:
                    if st.button(f"📝 Editar", key=f"editar_{projeto['id']}", use_container_width=True):
                        st.session_state[PROJETO_SELECIONADO_KEY] = projeto
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_projeto'
                        st.rerun()
                with btn_cols_card[1]:
                    if st.button(f"🗑️ Excluir", key=f"excluir_{projeto['id']}", use_container_width=True):
                        st.session_state['projeto_para_excluir'] = projeto
                        st.rerun()

    if 'projeto_para_excluir' in st.session_state:
        projeto_excluir = st.session_state['projeto_para_excluir']
        st.warning(f"Tem certeza que deseja excluir o projeto '{projeto_excluir.get('nome')}'? Esta ação não pode ser desfeita.")
        col_confirm1, col_confirm2, _ = st.columns([1,1,2]) 
        with col_confirm1:
            if st.button("Sim, Excluir", type="primary", key=f"confirm_excluir_{projeto_excluir['id']}"):
                try:
                    db = firestore.client()
                    db.collection('projetos').document(projeto_excluir['id']).delete()
                    st.success(f"Projeto '{projeto_excluir.get('nome')}' excluído com sucesso.")
                    del st.session_state['projeto_para_excluir']
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir projeto: {e}")
                    if 'projeto_para_excluir' in st.session_state: 
                        del st.session_state['projeto_para_excluir']
        with col_confirm2:
            if st.button("Cancelar", key=f"cancel_excluir_{projeto_excluir['id']}"):
                del st.session_state['projeto_para_excluir']
                st.rerun()

def pagina_novo_projeto():
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
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {str(e)}")
    
    if st.button("⬅️ Voltar para Projetos"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun()

# def pagina_detalhes_projeto(): (Definição da função comentada, como no original)
# ...

def main():
    print(f"DEBUG main(): Verificando FIREBASE_APP_INITIALIZED = {FIREBASE_APP_INITIALIZED}. Erro capturado: {FIREBASE_INIT_ERROR_MESSAGE}")
    
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
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'

    if not st.session_state[AUTENTICADO_SESSION_KEY]:
        current_page = st.session_state[PAGINA_ATUAL_SESSION_KEY]
        if current_page == 'reset_password':
            pagina_reset_password() 
        elif current_page == 'cadastro':
            pagina_cadastro() 
        else: 
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            pagina_login()
    else:
        current_page = st.session_state[PAGINA_ATUAL_SESSION_KEY]
        
        if not FIREBASE_APP_INITIALIZED and current_page not in ['login']: 
            st.error("Erro de conexão com o Firebase. Algumas funcionalidades podem não estar disponíveis.")
            if st.button("Tentar reconectar / Voltar ao Login"):
                st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
                st.rerun()
            return

        if current_page == 'projetos':
            pagina_projetos()
        elif current_page == 'novo_projeto':
            pagina_novo_projeto()
        elif current_page == 'editar_projeto':
            pagina_editar_projeto_view() 
        elif current_page == 'cadastro_edital':
            pagina_cadastro_edital() 
        else:
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()

if __name__ == '__main__':
    main()
