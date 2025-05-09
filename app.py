import tempfile
import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

from loaders import *

TIPOS_ARQUIVOS_VALIDOS = [
    'Site', 'Youtube', 'Pdf', 'Csv', 'Txt'
]

CONFIG_MODELOS = {'Groq': 
                        {'modelos': ['llama-3-70b-8192', 'mixtral-8x7b-32768', 'gemma-7b-it'],
                         'chat': ChatGroq},
                  'OpenAI': 
                        {'modelos': ['gpt-4-turbo', 'gpt-4', 'gpt-3.5-turbo'],
                         'chat': ChatOpenAI}}

MEMORIA = ConversationBufferMemory()

import os
import streamlit as st
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth

# Carregar variáveis de ambiente
load_dotenv()

# Verificar se todas as variáveis necessárias estão presentes
required_env_vars = [
    'FIREBASE_TYPE',
    'FIREBASE_PROJECT_ID',
    'FIREBASE_PRIVATE_KEY_ID',
    'FIREBASE_PRIVATE_KEY',
    'FIREBASE_CLIENT_EMAIL',
    'FIREBASE_CLIENT_ID',
    'FIREBASE_AUTH_URI',
    'FIREBASE_TOKEN_URI',
    'FIREBASE_AUTH_PROVIDER_CERT_URL',
    'FIREBASE_CLIENT_CERT_URL'
]

missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:  # Você tinha escrito "missing_vars" como "missing_vars"
    raise ValueError(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")

# Construir o dicionário de configuração do Firebase
firebase_config = {
    "type": os.getenv("FIREBASE_TYPE"),
    "project_id": os.getenv("FIREBASE_PROJECT_ID"),
    "private_key_id": os.getenv("FIREBASE_PRIVATE_KEY_ID"),
    "private_key": os.getenv("FIREBASE_PRIVATE_KEY").replace('\\n', '\n'),
    "client_email": os.getenv("FIREBASE_CLIENT_EMAIL"),
    "client_id": os.getenv("FIREBASE_CLIENT_ID"),
    "auth_uri": os.getenv("FIREBASE_AUTH_URI"),
    "token_uri": os.getenv("FIREBASE_TOKEN_URI"),
    "auth_provider_x509_cert_url": os.getenv("FIREBASE_AUTH_PROVIDER_CERT_URL"),
    "client_x509_cert_url": os.getenv("FIREBASE_CLIENT_CERT_URL")
}

# Inicializar o Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_config)
    firebase_admin.initialize_app(cred)
    print("Firebase Admin SDK inicializado com sucesso!")

def pagina_login():
    """Página de login com Firebase"""
    st.title("🔐 Oráculo Cultural - Login")
    st.markdown("---")
    
    with st.form("login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        submitted = st.form_submit_button("Entrar")
        
        if submitted:
            try:
                # Autenticação com Firebase
                user = auth.get_user_by_email(email)
                # Simulação de verificação de senha (em produção, use Firebase Auth)
                st.session_state['user'] = {
                    'email': email,
                    'uid': user.uid
                }
                st.session_state['autenticado'] = True
                st.success("Login bem-sucedido!")
                st.rerun()
            except Exception as e:
                st.error(f"Erro no login: {e}")


def pagina_inicial():
    st.title('Oráculo Cultural - Edital Vale')
    st.header('Bem-vindo ao assistente para projetos culturais', divider=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Já tenho um projeto', use_container_width=True):
            st.session_state['fluxo'] = 'projeto_existente'
            st.rerun()
    with col2:
        if st.button('Quero criar um novo projeto', use_container_width=True):
            st.session_state['fluxo'] = 'novo_projeto'
            st.rerun()

def carrega_arquivos(tipo_arquivo, arquivo):
    if tipo_arquivo == 'Site':
        documento = carrega_site(arquivo)
    elif tipo_arquivo == 'Youtube':
        documento = carrega_youtube(arquivo)
    elif tipo_arquivo == 'Pdf':
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_pdf(nome_temp)
    elif tipo_arquivo == 'Csv':
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_csv(nome_temp)
    elif tipo_arquivo == 'Txt':
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp:
            temp.write(arquivo.read())
            nome_temp = temp.name
        documento = carrega_txt(nome_temp)
    return documento

def carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo):
    documento = carrega_arquivos(tipo_arquivo, arquivo)

    system_message = '''Você é um criador de projetos culturais com grande eficiência.
    Você possui acesso às seguintes informações vindas 
    de um documento {}: {}

    ####
    {}
    ####

    Utilize as informações fornecidas para basear as suas respostas.

    Sempre que houver $ na sua saída, substita por S.

    Se a informação do documento for algo como "Just a moment...Enable JavaScript and cookies to continue" 
    sugira ao usuário carregar novamente o Oráculo!'''.format(tipo_arquivo, arquivo if isinstance(arquivo, str) else "arquivo carregado", documento)

    template = ChatPromptTemplate.from_messages([
        ('system', system_message),
        ('placeholder', '{chat_history}'),
        ('user', '{input}')
    ])
    chat = CONFIG_MODELOS[provedor]['chat'](model=modelo, api_key=api_key)
    chain = template | chat

    st.session_state['chain'] = chain

def pagina_chat_existente():
    st.header('🤖 Oráculo - Aperfeiçoamento de Projeto', divider=True)

    chain = st.session_state.get('chain')
    if chain is None:
        st.error('Por favor, carregue o Oráculo primeiro')
        st.stop()

    memoria = st.session_state.get('memoria', MEMORIA)
    for mensagem in memoria.buffer_as_messages:
        chat = st.chat_message(mensagem.type)
        chat.markdown(mensagem.content)

    input_usuario = st.chat_input('Fale com o oráculo sobre seu projeto existente')
    if input_usuario:
        chat = st.chat_message('human')
        chat.markdown(input_usuario)

        chat = st.chat_message('ai')
        resposta = chat.write_stream(chain.stream({
            'input': input_usuario, 
            'chat_history': memoria.buffer_as_messages
            }))
        
        memoria.chat_memory.add_user_message(input_usuario)
        memoria.chat_memory.add_ai_message(resposta)
        st.session_state['memoria'] = memoria

def pagina_chat_novo():
    st.header('🤖 Oráculo - Criação de Novo Projeto', divider=True)
    
    # Etapa 1: Coleta de informações básicas
    with st.expander("📋 Informações Básicas do Projeto"):
        nome_projeto = st.text_input("Nome do Projeto")
        area_cultural = st.selectbox("Área Cultural", ["Artes Visuais", "Música", "Teatro", "Dança", "Literatura", "Cinema", "Cultura Popular", "Outros"])
        localizacao = st.text_input("Localização (Cidade/Estado)")
        publico_alvo = st.text_input("Público-Alvo")
    
    # Etapa 2: Upload de materiais de referência
    with st.expander("📂 Materiais de Referência"):
        st.write("Carregue materiais que possam servir de referência para seu projeto")
        tipo_arquivo = st.selectbox('Selecione o tipo de material', TIPOS_ARQUIVOS_VALIDOS)
        if tipo_arquivo == 'Site':
            arquivo = st.text_input('Digite a url do site')
        elif tipo_arquivo == 'Youtube':
            arquivo = st.text_input('Digite a url do vídeo')
        else:
            extensao = tipo_arquivo.lower()
            arquivo = st.file_uploader(f'Faça o upload do arquivo {extensao}', type=[f'.{extensao}'])
    
    # Etapa 3: Configuração do assistente
    with st.expander("⚙️ Configuração do Oráculo"):
        provedor = st.selectbox('Selecione o provedor do modelo', CONFIG_MODELOS.keys())
        modelo = st.selectbox('Selecione o modelo', CONFIG_MODELOS[provedor]['modelos'])
        api_key = st.text_input(
            f'Adicione a api key para o provedor {provedor}',
            value=st.session_state.get(f'api_key_{provedor}'))
        st.session_state[f'api_key_{provedor}'] = api_key
    
    if st.button('Inicializar Oráculo Criativo', use_container_width=True):
        if nome_projeto and area_cultural and localizacao:
            st.session_state['info_projeto'] = {
                'nome': nome_projeto,
                'area': area_cultural,
                'local': localizacao,
                'publico': publico_alvo
            }
            if arquivo:
                carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo)
            st.success("Oráculo pronto para ajudar na criação do seu projeto!")
        else:
            st.warning("Por favor, preencha todas as informações básicas do projeto")
    
    if 'info_projeto' in st.session_state:
        st.divider()
        st.subheader("Assistente de Criação")
        
        chain = st.session_state.get('chain')
        memoria = st.session_state.get('memoria', MEMORIA)
        
        for mensagem in memoria.buffer_as_messages:
            chat = st.chat_message(mensagem.type)
            chat.markdown(mensagem.content)

        input_usuario = st.chat_input('Descreva sua ideia ou faça perguntas sobre a criação do projeto')
        if input_usuario:
            chat = st.chat_message('human')
            chat.markdown(input_usuario)

            chat = st.chat_message('ai')
            resposta = chat.write_stream(chain.stream({
                'input': input_usuario, 
                'chat_history': memoria.buffer_as_messages
                }))
            
            memoria.chat_memory.add_user_message(input_usuario)
            memoria.chat_memory.add_ai_message(resposta)
            st.session_state['memoria'] = memoria

def sidebar():
    if st.session_state.get('fluxo') == 'projeto_existente':
        tabs = st.tabs(['Upload de Arquivos', 'Seleção de Modelos'])
        with tabs[0]:
            tipo_arquivo = st.selectbox('Selecione o tipo de arquivo', TIPOS_ARQUIVOS_VALIDOS)
            if tipo_arquivo == 'Site':
                arquivo = st.text_input('Digite a url do site')
            elif tipo_arquivo == 'Youtube':
                arquivo = st.text_input('Digite a url do vídeo')
            else:
                extensao = tipo_arquivo.lower()
                arquivo = st.file_uploader(f'Faça o upload do arquivo {extensao}', type=[f'.{extensao}'])
        with tabs[1]:
            provedor = st.selectbox('Selecione o provedor dos modelo', CONFIG_MODELOS.keys())
            modelo = st.selectbox('Selecione o modelo', CONFIG_MODELOS[provedor]['modelos'])
            api_key = st.text_input(
                f'Adicione a api key para o provedor {provedor}',
                value=st.session_state.get(f'api_key_{provedor}'))
            st.session_state[f'api_key_{provedor}'] = api_key
        
        if st.button('Inicializar Oráculo', use_container_width=True):
            if arquivo:
                carrega_modelo(provedor, modelo, api_key, tipo_arquivo, arquivo)
            else:
                st.warning("Por favor, carregue algum material de referência")
        if st.button('Apagar Histórico de Conversa', use_container_width=True):
            st.session_state['memoria'] = MEMORIA

def main():
    # Remova a linha st.set_page_config() daqui
    if not st.session_state.get('autenticado'):
        pagina_login()
    else:
        st.success(f"Bem-vindo, {st.session_state.user['email']}!")
        if st.button("Sair"):
            st.session_state.clear()
            st.rerun()

    if 'fluxo' not in st.session_state:
        pagina_inicial()
    else:
        if st.button("← Voltar para tela inicial"):
            st.session_state.pop('fluxo', None)
            if 'memoria' in st.session_state:
                st.session_state['memoria'] = MEMORIA
            if 'chain' in st.session_state:
                st.session_state.pop('chain')
            st.rerun()
        
        if st.session_state['fluxo'] == 'projeto_existente':
            with st.sidebar:
                sidebar()
            pagina_chat_existente()
        elif st.session_state['fluxo'] == 'novo_projeto':
            pagina_chat_novo()

if __name__ == '__main__':
    st.set_page_config(page_title="Oráculo Cultural - Edital Vale", page_icon="🎭")
    main()