import tempfile
import os
import streamlit as st
from langchain.memory import ConversationBufferMemory
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth

# Configuração inicial
st.set_page_config(
    page_title="Oráculo Cultural - Edital Vale", 
    page_icon="🎭",
    layout="wide"
)

# Carrega variáveis de ambiente
load_dotenv()

# Constantes
TIPOS_ARQUIVOS_VALIDOS = ['Site', 'Youtube', 'Pdf', 'Csv', 'Txt']
MODELO_PADRAO = "gpt-4-turbo"
MEMORIA = ConversationBufferMemory()

# Inicialização do Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_path = "config/firebase-service-account.json"
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True

# Página de Login
def pagina_login():
    st.title("🔐 Oráculo Cultural - Login")
    
    with st.form("login_form"):
        email = st.text_input("E-mail")
        password = st.text_input("Senha", type="password")
        
        if st.form_submit_button("Entrar"):
            try:
                user = auth.get_user_by_email(email)
                st.session_state.update({
                    'user': {'email': email, 'uid': user.uid},
                    'autenticado': True
                })
                st.rerun()  # Atualizado para st.rerun()
            except Exception as e:
                st.error(f"Erro no login: {str(e)}")

# Página Inicial após Login
def pagina_inicial():
    st.title(f'Bem-vindo, {st.session_state.user["email"]}!')
    
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()  # Atualizado para st.rerun()
    
    st.header('Escolha o tipo de projeto', divider=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Já tenho um projeto', use_container_width=True):
            st.session_state['fluxo'] = 'projeto_existente'
            st.rerun()  # Atualizado para st.rerun()
    with col2:
        if st.button('Quero criar um novo projeto', use_container_width=True):
            st.session_state['fluxo'] = 'novo_projeto'
            st.rerun()  # Atualizado para st.rerun()

# Páginas de Projetos
def pagina_projeto_existente():
    st.header('📤 Envie seu projeto para análise')
    
    arquivo = st.file_uploader("Envie seu projeto em PDF", type=["pdf"])
    
    if arquivo:
        with st.spinner('Processando seu projeto...'):
            try:
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp:
                    temp.write(arquivo.read())
                    texto_pdf = carrega_pdf(temp.name)
                
                st.session_state['texto_projeto'] = texto_pdf
                st.success("Projeto carregado com sucesso!")
                
                carrega_modelo("Pdf", texto_pdf)
                
            except Exception as e:
                st.error(f"Erro ao processar PDF: {str(e)}")

def pagina_novo_projeto():
    st.header('✨ Crie um novo projeto')
    
    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto")
        descricao = st.text_area("Descrição")
        categoria = st.selectbox("Categoria", ["Artes", "Música", "Teatro"])
        
        if st.form_submit_button("Salvar Projeto"):
            st.session_state['projeto'] = {
                'nome': nome,
                'descricao': descricao,
                'categoria': categoria
            }
            st.success("Projeto criado com sucesso!")

# Fluxo Principal
def main():
    if not initialize_firebase():
        st.stop()

    # Inicializa estado da sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    # Verificação de autenticação
    if not st.session_state.get('autenticado'):
        pagina_login()
        st.stop()  # Impede renderização dupla
    
    # Páginas autenticadas
    if 'fluxo' not in st.session_state:
        pagina_inicial()
    else:
        if st.session_state['fluxo'] == 'projeto_existente':
            pagina_projeto_existente()
        elif st.session_state['fluxo'] == 'novo_projeto':
            pagina_novo_projeto()

if __name__ == '__main__':
    main()