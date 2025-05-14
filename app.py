import tempfile
import os
import streamlit as st
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from models import (
    get_llm,
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa)
from loaders import carrega_pdf
from services.firestore_service import initialize_firebase
from paginas.pagina_editar_projeto import pagina_editar_projeto as pagina_editar_projeto_view


initialize_firebase()

# Configuração inicial
# Configuração inicial
st.set_page_config(
    page_title="Oráculo Cultural - Edital Vale", 
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# CSS customizado com melhorias de responsividade
st.markdown("""
    <style>
            Esconde completamente o menu lateral padrão e ícone de hamburger */
        [data-testid="stSidebarNav"],
        [data-testid="collapsedControl"] {
            display: none;
        }
        
        /* Esconde o menu padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Remove padding extra */
        .stApp {
            padding-top: 1rem;
        }
        /* Esconde o menu padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Botão de login */
        .stButton>button {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            width: 100%;
        }
        
        /* Campos de input */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            padding: 0.5rem;
        }

        /* Ajustes de responsividade */
        @media screen and (min-width: 1024px) {
            .main .block-container {
                max-width: 90%;
                padding-left: 2rem;
                padding-right: 2rem;
            }
        }

        /* Estilo para cartões de projetos */
        .project-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
            
            
""", unsafe_allow_html=True)

# Carrega variáveis de ambiente
load_dotenv()

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

# Função para recuperar projetos do usuário
def get_user_projects(user_id):
    try:
        db = firestore.client()
        projetos_ref = db.collection('projetos').where('user_id', '==', user_id)
        projetos = projetos_ref.stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in projetos]
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []

# Página de Login
import streamlit as st
import firebase_admin
from firebase_admin import auth

import streamlit as st
import firebase_admin # Assuming firebase_admin is initialized elsewhere if needed by auth
from firebase_admin import auth

def pagina_login():
    st.markdown(
        """
        <style>
            body {
                background-color: #f0f2f5; /* Cor de fundo geral da página */
            }
            .login-container {
                background-color: rgba(255, 255, 255, 0.9); /* Fundo branco semi-transparente */
                padding: 2rem;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                width: 80%; /* Largura do container */
                max-width: 400px; /* Largura máxima */
                margin: 100px auto; /* Centralizar vertical e horizontalmente */
                text-align: center;
            }
            .login-container img {
                width: 150px; /* Ajuste o tamanho do logo */
                margin-bottom: 1rem;
            }
            .login-container h2 {
                color: #333;
                margin-bottom: 1.5rem;
            }
            .login-container input[type="text"],
            .login-container input[type="password"] {
                width: 100%;
                padding: 0.75rem;
                margin-bottom: 1rem;
                border: 1px solid #ccc;
                border-radius: 5px;
                box-sizing: border-box; /* Para que o padding não aumente a largura */
            }
            .login-container button {
                background-color: #e74c3c; /* Cor do botão (exemplo) */
                color: white;
                border: none;
                padding: 0.75rem 1rem;
                border-radius: 5px;
                cursor: pointer;
                width: 100%;
            }
            .login-container button:hover {
                background-color: #c0392b; /* Cor do botão no hover (exemplo) */
            }
            .login-container .forgot-password {
                margin-top: 0.5rem;
                font-size: 0.9rem;
            }
            .login-container .signup-link {
                margin-top: 1rem;
                font-size: 0.9rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    with st.container(): # Outer container for column layout
        col1, col2, col3 = st.columns([1, 3, 1])

        with col2: # Middle column for the login box
            # Use st.markdown to create a div with the class "login-container".
            # This div will be styled by the .login-container CSS rules.
            # The original st.container(border=True, classes="login-container") is replaced by this approach.
            st.markdown('<div class="login-container">', unsafe_allow_html=True)
            
            st.image("assets/logo_edital_vale.jpg", width=150) # Ensure path is correct
            st.title("Acesso ao Oráculo Cultural") # st.title might be too large, consider st.header or st.subheader

            with st.form("login_form"):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("Entrar", use_container_width=True)

                if submitted:
                    try:
                        # Ensure Firebase is initialized before calling auth functions
                        if not firebase_admin._apps:
                            # This is a fallback, ideally Firebase is initialized once globally
                            # Consider moving initialize_firebase() call to the top of main() or app startup
                            st.error("Firebase não inicializado. Por favor, contate o suporte.")
                        else:
                            user = auth.get_user_by_email(email)
                            # Assuming st.session_state is available
                            st.session_state.update({
                                'user': {'email': email, 'uid': user.uid},
                                'autenticado': True,
                                'pagina_atual': 'projetos'
                            })
                            st.rerun()
                    except Exception as e:
                        st.error(f"Falha no login: Verifique seu e-mail e senha. Detalhe: {str(e)}")
            
            st.markdown('<p class="forgot-password"><a href="#">Esqueci minha senha</a></p>', unsafe_allow_html=True)
            st.markdown('<p class="signup-link">Novo por aqui? <a href="#">Cadastre-se</a></p>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True) # Close the div.login-container
# Página de Projetos
def pagina_projetos():
    st.title(f'Bem-vindo, {st.session_state.user["email"]}!')
    
    if st.button("Sair", key="logout_button"):
        st.session_state.clear()
        st.rerun()
    
    projetos = get_user_projects(st.session_state.user['uid'])
    
    st.header('Meus Projetos', divider=True)
    
    if not projetos:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3>Você ainda não tem projetos</h3>
                <p>Comece criando seu primeiro projeto!</p>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("Criar Primeiro Projeto", use_container_width=True, type="primary"):
                st.session_state['pagina_atual'] = 'novo_projeto'
                st.rerun()
    else:
        st.markdown('<div style="text-align: right; margin-bottom: 1rem;">', unsafe_allow_html=True)
        if st.button("+ Criar Novo Projeto"):
            st.session_state['pagina_atual'] = 'novo_projeto'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        cols = st.columns(3)
        for i, projeto in enumerate(projetos):
            col = cols[i % 3]
            with col:
                with st.container(border=True):
                    st.markdown(f"""
                        <div class="project-card">
                            <h3>{projeto.get('nome', 'Projeto sem nome')}</h3>
                            <p><strong>Categoria:</strong> {projeto.get('categoria', 'Não definida')}</p>
                            <p>{projeto.get('descricao', 'Sem descrição')[:100]}...</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Editar #{projeto['id']}", key=f"editar_{projeto['id']}"):
                            st.session_state['projeto_selecionado'] = projeto
                            st.session_state['pagina_atual'] = 'editar_projeto'
                            st.rerun()
                    with col2:
                        if st.button(f"Detalhes #{projeto['id']}", key=f"detalhes_{projeto['id']}"):
                            st.session_state['projeto_selecionado'] = projeto
                            st.session_state['pagina_atual'] = 'detalhes_projeto'
                            st.rerun()
# Página para Criar Novo Projeto
def pagina_novo_projeto():
    st.header('✨ Criar Novo Projeto')
    
    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto")
        descricao = st.text_area("Descrição do Projeto")
        categoria = st.selectbox("Categoria", [
            "Artes Visuais", 
            "Música", 
            "Teatro", 
            "Dança", 
            "Cinema", 
            "Literatura"
        ])
        
        if st.form_submit_button("Salvar Projeto"):
            try:
                db = firestore.client()
                novo_projeto = {
                    'nome': nome,
                    'descricao': descricao,
                    'categoria': categoria,
                    'user_id': st.session_state.user['uid'],
                    'data_criacao': firestore.SERVER_TIMESTAMP
                }
                
                # Salvar projeto no Firestore
                doc_ref = db.collection('projetos').add(novo_projeto)
                
                st.success(f"Projeto '{nome}' criado com sucesso!")
                
                # Redirecionar para página de projetos
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar projeto: {str(e)}")

# Função para editar projeto
def pagina_editar_projeto():
    pagina_editar_projeto_view()
  

# Função para mostrar detalhes do projeto
def pagina_detalhes_projeto():
    projeto = st.session_state.get('projeto_selecionado', {})
    
    st.header(f'🔍 Detalhes do Projeto: {projeto.get("nome", "Sem Nome")}')
    
    # Opções de geração de documentos
    st.header("📑 Geração de Documentos", divider=True)
    
    # Verificar se o projeto tem um PDF carregado
    if 'texto_projeto' not in st.session_state:
        st.info("⚠️ Carregue um PDF do projeto para gerar documentos.")
        arquivo = st.file_uploader("Selecione o arquivo PDF do projeto", type=["pdf"])

        if arquivo:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as temp:
                temp.write(arquivo.read())
                texto_projeto = carrega_pdf(temp.name)
                st.session_state['texto_projeto'] = texto_projeto
                st.success("✅ Documento carregado com sucesso!")
    
    if 'texto_projeto' in st.session_state:
        # Tabs para geração de documentos
        tabs = st.tabs(["📝 Resumo", "💰 Orçamento", "📅 Cronograma", "🎯 Objetivos", "📚 Justificativa"])

        with tabs[0]:
            if st.button("Gerar Resumo"):
                with st.spinner("Criando..."):
                    st.session_state['resumo'] = gerar_resumo_projeto(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Resumo pronto.")
            if 'resumo' in st.session_state:
                st.subheader("📝 Resumo")
                st.write(st.session_state['resumo'])

        with tabs[1]:
            if st.button("Gerar Orçamento"):
                with st.spinner("Criando..."):
                    st.session_state['orcamento'] = gerar_orcamento(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Orçamento pronto.")
            if 'orcamento' in st.session_state:
                st.subheader("💰 Orçamento")
                st.write(st.session_state['orcamento'])

        with tabs[2]:
            if st.button("Gerar Cronograma"):
                with st.spinner("Criando..."):
                    st.session_state['cronograma'] = gerar_cronograma(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Cronograma pronto.")
            if 'cronograma' in st.session_state:
                st.subheader("📅 Cronograma")
                st.write(st.session_state['cronograma'])

        with tabs[3]:
            if st.button("Gerar Objetivos SMART"):
                with st.spinner("Criando..."):
                    st.session_state['objetivos'] = gerar_objetivos(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Objetivos prontos.")
            if 'objetivos' in st.session_state:
                st.subheader("🎯 Objetivos")
                st.write(st.session_state['objetivos'])

        with tabs[4]:
            if st.button("Gerar Justificativa Técnica"):
                with st.spinner("Criando..."):
                    st.session_state['justificativa'] = gerar_justificativa(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Justificativa pronta.")
            if 'justificativa' in st.session_state:
                st.subheader("📚 Justificativa Técnica")
                st.write(st.session_state['justificativa'])

        # Área de download
        st.divider()
        with st.expander("💾 Baixar Documentos Gerados"):
            doc_cols = st.columns(4)
            if 'resumo' in st.session_state:
                doc_cols[0].download_button("⏬ Resumo", st.session_state['resumo'], "resumo.txt")
            if 'orcamento' in st.session_state:
                doc_cols[1].download_button("⏬ Orçamento", st.session_state['orcamento'], "orcamento.txt")
            if 'cronograma' in st.session_state:
                doc_cols[2].download_button("⏬ Cronograma", st.session_state['cronograma'], "cronograma.txt")
            if 'objetivos' in st.session_state:
                doc_cols[3].download_button("⏬ Objetivos", st.session_state['objetivos'], "objetivos.txt")
            if 'justificativa' in st.session_state:
                st.download_button("⏬ Justificativa", st.session_state['justificativa'], "justificativa.txt")
    
    # Botão para voltar
    if st.button("Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun()

# Fluxo Principal
def main():
    if not initialize_firebase():
        st.stop()

    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'pagina_atual' not in st.session_state:
        st.session_state.pagina_atual = 'login'

    if not st.session_state.autenticado:
        pagina_login()
    else:
        if st.session_state.pagina_atual == 'projetos':
            pagina_projetos()
        elif st.session_state.pagina_atual == 'novo_projeto':
            pagina_novo_projeto()
        elif st.session_state.pagina_atual == 'editar_projeto':
            pagina_editar_projeto_view()  # Chamada corrigida
        elif st.session_state.pagina_atual == 'detalhes_projeto':
            pagina_detalhes_projeto()
        else:
            st.session_state.pagina_atual = 'projetos'
            st.rerun()

if __name__ == '__main__':
    main()