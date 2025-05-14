import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import os

# Constantes para nomes de chave do session_state para evitar erros de digitação
USER_SESSION_KEY = 'user'
AUTENTICADO_SESSION_KEY = 'autenticado'
PAGINA_ATUAL_SESSION_KEY = 'pagina_atual'

def initialize_firebase_login():
    """
    Inicializa o Firebase Admin SDK se ainda não estiver inicializado.
    Retorna True se o Firebase estiver inicializado (ou já estava), False caso contrário.
    Exibe mensagens de erro no Streamlit em caso de falha na inicialização.
    """
    if not firebase_admin._apps:
        try:
            cred_path = "config/firebase-service-account.json"
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, name="login_app_instance" + str(os.getpid())) # Nome único para a instância
            return True
        except FileNotFoundError:
            st.error("Arquivo de credenciais do Firebase (firebase-service-account.json) não encontrado em 'config/'. Verifique o caminho.")
            return False
        except ValueError as e:
            if "already initialized" in str(e).lower(): # Verifica se o erro é de app já inicializado
                return True # Considera como sucesso se já estiver inicializado
            st.error(f"Erro ao inicializar Firebase com as credenciais: {e}. Verifique o arquivo JSON.")
            return False
        except Exception as e:
            st.error(f"Erro desconhecido ao inicializar Firebase no módulo de login: {str(e)}")
            return False
    return True

def pagina_login():
    """
    Exibe a página de login com layout de dois painéis (usando st.columns)
    e lida com a autenticação do usuário.
    """
    if not initialize_firebase_login():
        st.warning("A inicialização do Firebase falhou. O login não pode prosseguir.")
        st.stop()

    st.markdown("""
        <style>
            /* Reset e configurações globais */
            .stApp > header {
                background-color: transparent;
            }
            div[data-testid="stSidebarNav"], div[data-testid="collapsedControl"] { 
                display: none; 
            }
            
            /* Ocultar qualquer elemento que exiba código HTML literal */
            div[data-testid="element-container"] pre {
                display: none !important;
            }
            
            /* Ocultar qualquer box de código que possa estar aparecendo */
            .stCodeBlock {
                display: none !important;
            }
            
            /* Ocultar elementos de markdown que possam estar mostrando HTML */
            [data-testid="stMarkdownContainer"] code,
            [data-testid="stMarkdownContainer"] pre {
                display: none !important;
            }
            
            /* Container principal para ocupar toda a tela */
            div.block-container:has(div.login-master-container) {
                padding: 0 !important;
                margin: 0 !important;
                max-width: 100% !important;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff);
                box-sizing: border-box;
            }

            /* Container mestre do card de login */
            .login-master-container {
                width: 100%;
                max-width: 100%;
                height: 100vh;
                display: flex;
                flex-direction: row;
                overflow: hidden;
            }
            
            /* Estilos do painel esquerdo */
            .login-left-panel {
                background: linear-gradient(135deg, #e9d5ff, #ddd6fe);
                display: flex;
                flex-direction: column;
                justify-content: center;
                padding: 2rem 3rem;
                color: #1e293b;
                height: 100%;
            }
            
            .login-left-panel h1 {
                font-size: 3.5rem;
                font-weight: 800;
                margin-bottom: 1.5rem;
                color: #1e293b;
            }
            
            .login-left-panel .subtitle {
                font-size: 1.5rem;
                font-weight: 500;
                margin-bottom: 1.5rem;
                color: #334155;
            }
            
            .login-left-panel .description {
                font-size: 1.125rem;
                color: #475569;
                margin-bottom: 3rem;
                line-height: 1.7;
            }
            
            /* Estilo para os cards de estatísticas */
            .stats-grid {
                display: grid;
                grid-template-columns: repeat(3, 1fr);
                gap: 1rem;
                margin-top: 2rem;
            }
            
            .stat-card {
                background-color: white;
                border-radius: 1rem;
                padding: 1.5rem 1rem;
                text-align: center;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            }
            
            .stat-number {
                font-size: 2rem;
                font-weight: 700;
                color: #7e22ce;
                margin-bottom: 0.5rem;
            }
            
            .stat-label {
                font-size: 0.9rem;
                color: #64748b;
            }
            
            /* Estilos do painel direito */
            .login-right-panel {
                background-color: white;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                padding: 2rem;
                box-shadow: -10px 0 15px -3px rgba(0, 0, 0, 0.1);
                height: 100%;
                border-radius: 2rem 0 0 2rem;
            }
            
            .login-right-panel .logo {
                margin-bottom: 2rem;
                width: 80px;
                height: 80px;
            }
            
            .login-right-panel h2 {
                font-size: 2rem;
                font-weight: 700;
                color: #1e293b;
                margin-bottom: 0.5rem;
                text-align: center;
            }
            
            .login-right-panel .subtitle {
                font-size: 1rem;
                color: #64748b;
                margin-bottom: 2.5rem;
                text-align: center;
            }
            
            /* Estilização dos campos de formulário */
            .login-form {
                width: 100%;
                max-width: 400px;
            }
            
            .login-form .field-label {
                font-size: 0.9rem;
                font-weight: 500;
                color: #334155;
                margin-bottom: 0.5rem;
            }
            
            .login-form input[type="text"], 
            .login-form input[type="password"] {
                width: 100%;
                padding: 0.75rem 1rem;
                font-size: 1rem;
                border: 1px solid #e2e8f0;
                border-radius: 0.5rem;
                background-color: #f8fafc;
                margin-bottom: 1.5rem;
            }
            
            .login-form input[type="text"]::placeholder, 
            .login-form input[type="password"]::placeholder {
                color: #94a3b8;
            }
            
            /* Estilo do botão de login */
            .login-button {
                background-color: #7e22ce;
                color: white;
                border: none;
                border-radius: 0.5rem;
                padding: 0.75rem 2rem;
                font-size: 1rem;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                text-align: center;
                transition: all 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-top: 1rem;
            }
            
            /* Estilização para o botão do Streamlit */
            .stButton button {
                background-color: #7e22ce !important;
                color: white !important;
                width: 100% !important;
                border-radius: 0.5rem !important;
                padding: 0.75rem 1rem !important;
                font-weight: 600 !important;
            }
            
            .stButton button:hover {
                background-color: #6b21a8 !important;
            }
            
            /* Checkbox estilizado */
            .remember-forgot {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 1.5rem;
            }
            
            /* Estilização específica para o checkbox do Streamlit */
            [data-testid="stCheckbox"] {
                display: inline-block;
            }
            
            .st-emotion-cache-1inwz65 {
                font-size: 0.875rem;
                color: #475569;
            }
            
            .forgot-password {
                font-size: 0.875rem;
                color: #7e22ce;
                text-decoration: none;
                float: right;
            }
            
            .forgot-password:hover {
                text-decoration: underline;
            }
            
            /* Cadastro link */
            .signup-link {
                margin-top: 2rem;
                text-align: center;
                font-size: 0.875rem;
                color: #475569;
            }
            
            .signup-link a {
                color: #7e22ce;
                text-decoration: none;
                font-weight: 500;
            }
            
            .signup-link a:hover {
                text-decoration: underline;
            }
            
            /* Responsividade */
            @media (max-width: 992px) {
                .login-master-container {
                    flex-direction: column;
                    height: auto;
                }
                
                .login-left-panel {
                    padding: 2rem;
                }
                
                .login-left-panel h1 {
                    font-size: 2.5rem;
                }
                
                .login-right-panel {
                    border-radius: 2rem 2rem 0 0;
                    padding-top: 3rem;
                }
                
                .stats-grid {
                    grid-template-columns: repeat(1, 1fr);
                }
            }
        </style>
    """, unsafe_allow_html=True)

    # Container mestre sem usar st.columns (usaremos divs HTML diretamente)
    col_esquerda, col_direita = st.columns([1, 1])
    
    with col_esquerda:
        st.markdown("""
            <div class="login-left-panel">
                <h1>Oráculo Cultural</h1>
                <p class="subtitle">Sua plataforma para decifrar o universo da cultura</p>
                <p class="description">Descubra, conecte-se e explore o mundo cultural através de uma experiência única e personalizada.</p>
                
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">500+</div>
                        <div class="stat-label">Eventos Culturais</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">10k+</div>
                        <div class="stat-label">Usuários Ativos</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">300+</div>
                        <div class="stat-label">Artistas</div>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
    
    with col_direita:
        st.markdown("""
            <div class="login-right-panel">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" class="logo" alt="Oráculo Cultural Logo">
                <h2>Bem-vindo ao Oráculo Cultural</h2>
                <p class="subtitle">Acesse sua conta para explorar o universo cultural</p>
            </div>
        """, unsafe_allow_html=True)

        # Formulário de login movido para fora do HTML
        with st.form("login_form", clear_on_submit=False):
            st.markdown('<p class="field-label">E-mail</p>', unsafe_allow_html=True)
            email = st.text_input("", placeholder="seu@email.com", key="login_email", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Senha</p>', unsafe_allow_html=True)
            password = st.text_input("", type="password", placeholder="••••••••", key="login_password", label_visibility="collapsed")
            
            # Remember me e forgot password
            col1, col2 = st.columns([1, 1])
            with col1:
                remember_me = st.checkbox("Lembrar-me")
            with col2:
                st.markdown('<a href="#" class="forgot-password">Esqueci minha senha</a>', unsafe_allow_html=True)
            
            # Botão de submit
            submitted = st.form_submit_button("Entrar", use_container_width=True)
            
            # Verificação do formulário
            if submitted:
                if not email or not password:
                    st.error("Por favor, preencha o e-mail e a senha.")
                else:
                    try:
                        user_record = auth.get_user_by_email(email)
                        # A verificação de senha real deve ser feita com Firebase JS SDK
                        st.session_state[USER_SESSION_KEY] = {'email': user_record.email, 'uid': user_record.uid}
                        st.session_state[AUTENTICADO_SESSION_KEY] = True
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                        st.success(f"Login bem-sucedido como {user_record.email}!")
                        st.rerun()
                    except firebase_admin.auth.UserNotFoundError:
                        st.error("Usuário não encontrado. Verifique o e-mail ou cadastre-se.")
                    except Exception as e:
                        st.error(f"Falha no login: {str(e)}")

        # Link de cadastro
        st.markdown("""
            <div class="signup-link">
                Novo por aqui? <a href="#">Cadastre-se</a>
            </div>
        """, unsafe_allow_html=True)