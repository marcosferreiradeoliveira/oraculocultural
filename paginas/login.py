import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import os
import time
from services.firebase_init import initialize_firebase, get_error_message

# Constantes para nomes de chave do session_state
USER_SESSION_KEY = 'user'
AUTENTICADO_SESSION_KEY = 'autenticado'
PAGINA_ATUAL_SESSION_KEY = 'pagina_atual'
FIREBASE_INITIALIZED_KEY = 'firebase_initialized'

@st.cache_resource
def initialize_firebase_app():
    """Inicializa o Firebase com cache para melhor performance"""
    if not initialize_firebase():
        st.error(get_error_message())
        return False
    return True

def handle_login(email, senha):
    """Processa o login de forma otimizada"""
    if not email or not senha:
        st.error("Por favor, preencha o e-mail e a senha.")
        return False
    
    try:
        start_time = time.time()
        user = auth.get_user_by_email(email)
        
        st.session_state[USER_SESSION_KEY] = {
            'email': user.email,
            'uid': user.uid,
            'login_time': start_time
        }
        st.session_state[AUTENTICADO_SESSION_KEY] = True
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        
        end_time = time.time()
        st.toast(f"Bem-vindo, {user.email}! Login em {(end_time - start_time):.2f}s")
        return True
        
    except auth.UserNotFoundError:
        st.error("Usuário não encontrado. Verifique o e-mail.")
    except Exception as e:
        st.error(f"Erro no login: {str(e)}")
    
    return False

def pagina_login():
    """Exibe a página de login com layout moderno e otimizado"""
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase_app()
    if not firebase_app:
        return

    # --- CSS Styles (mantido igual) ---
    st.markdown("""
    <style>
        .stApp > header { display: none !important; }
        section.main.main { padding-top: 0 !important; margin-top: 0 !important; }
        .stApp section.main.main > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="block-container"]:first-child {
            padding-top: 0px !important;
        }
        div[data-testid="stSidebarNav"], div[data-testid="collapsedControl"] { display: none; }
        div[data-testid="element-container"] pre, .stCodeBlock,
        [data-testid="stMarkdownContainer"] code, [data-testid="stMarkdownContainer"] pre {
            display: none !important;
        }
        div.block-container:has(div.login-master-container) {
            padding: 0 !important; 
            margin: 0 !important; 
            max-width: 100% !important;
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh;
            background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff);
        }
        .login-master-container {
            width: 100%; max-width: 100%; height: 100vh;
            display: flex; flex-direction: row; overflow: hidden;
        }
        .login-left-panel {
            background: linear-gradient(135deg, #e9d5ff, #ddd6fe);
            display: flex; flex-direction: column; justify-content: center;
            padding: 2rem 3rem; color: #1e293b; height: 100%;
        }
        .login-left-panel h1 { font-size: 3.5rem; font-weight: 800; margin-bottom: 1.5rem; color: #1e293b; }
        .login-left-panel .subtitle { font-size: 1.5rem; font-weight: 500; margin-bottom: 1.5rem; color: #334155; }
        .login-left-panel .description { font-size: 1.125rem; color: #475569; margin-bottom: 3rem; line-height: 1.7; }
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem; }
        .stat-card {
            background-color: white; border-radius: 1rem; padding: 1.5rem 1rem; text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
        }
        .stat-number { font-size: 2rem; font-weight: 700; color: #7e22ce; margin-bottom: 0.5rem; }
        .stat-label { font-size: 0.9rem; color: #64748b; }
        .login-right-panel {
            background-color: white; display: flex; flex-direction: column;
            justify-content: center; align-items: center; padding: 2rem;
            box-shadow: -10px 0 15px -3px rgba(0,0,0,0.1);
            height: 100%; border-radius: 2rem 0 0 2rem;
        }
        .login-right-panel .logo { margin-bottom: 2rem; width: 80px; height: 80px; }
        .login-right-panel h2 { font-size: 2rem; font-weight: 700; color: #1e293b; margin-bottom: 0.5rem; text-align: center; }
        .login-right-panel .subtitle { font-size: 1rem; color: #64748b; margin-bottom: 2.5rem; text-align: center; }
        .login-form .field-label { font-size: 0.9rem; font-weight: 500; color: #334155; margin-bottom: 0.5rem; }
        .stButton button {
            background-color: #7e22ce !important; color: white !important;
            width: 100% !important; border-radius: 0.5rem !important;
            padding: 0.75rem 1rem !important; font-weight: 600 !important;
        }
        .stButton button:hover { background-color: #6b21a8 !important; }
        .forgot-password-button button {
            background-color: transparent !important; color: #7e22ce !important;
            border: none !important; padding: 0 !important;
            font-size: 0.875rem !important; font-weight: normal !important;
            text-decoration: none !important; width: auto !important; display: inline !important;
        }
        .forgot-password-button button:hover { text-decoration: underline !important; }
        .forgot-password-container {
            text-align: right; width: 100%; max-width: 400px;
            margin-top: -1rem; margin-bottom: 1.5rem;
        }
        .signup-link { margin-top: 2rem; text-align: center; font-size: 0.875rem; color: #475569; }
        .signup-link a { color: #7e22ce; text-decoration: none; font-weight: 500; }
        .signup-link a:hover { text-decoration: underline; }
        
        @media (max-width: 992px) {
            .login-master-container { flex-direction: column; height: auto; }
            .login-left-panel { padding: 2rem; }
            .login-left-panel h1 { font-size: 2.5rem; }
            .login-right-panel { border-radius: 2rem 2rem 0 0; padding-top: 3rem; }
            .stats-grid { grid-template-columns: repeat(1, 1fr); }
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Layout Principal (mantido igual) ---
    st.markdown('<div class="login-master-container">', unsafe_allow_html=True)
    
    col_esquerda, col_direita = st.columns([0.55, 0.45])

    with col_esquerda:
        st.markdown("""
            <div class="login-left-panel">
                <h1>Oráculo Cultural</h1>
                <p class="subtitle">Sua plataforma para decifrar o universo da cultura</p>
                <p class="description">Descubra, conecte-se e explore o mundo cultural através de uma experiência única e personalizada.</p>
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-number">500+</div><div class="stat-label">Eventos Culturais</div></div>
                    <div class="stat-card"><div class="stat-number">10k+</div><div class="stat-label">Usuários Ativos</div></div>
                    <div class="stat-card"><div class="stat-number">300+</div><div class="stat-label">Artistas</div></div>
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

        # Formulário de login otimizado
        with st.form("login_form_main", clear_on_submit=False):
            st.markdown('<p class="field-label">E-mail</p>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="seu@email.com", key="login_email", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Senha</p>', unsafe_allow_html=True)
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="login_senha", label_visibility="collapsed")
            
            st.checkbox("Lembrar-me", key="login_remember")
            
            login_submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if login_submit:
                with st.spinner("Autenticando..."):
                    if handle_login(email, senha):
                        st.rerun()

        # Link para reset de senha
        st.markdown('<div class="forgot-password-container">', unsafe_allow_html=True)
        if st.button("Esqueci minha senha", key="forgot_password_btn"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'reset_password'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Link de cadastro
        st.markdown('<div class="signup-link">', unsafe_allow_html=True)
        if st.button("Novo por aqui? Cadastre-se", key="signup_button"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'cadastro'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# Inicialização da sessão
if __name__ == '__main__':
    # Configuração inicial otimizada
    required_keys = {
        USER_SESSION_KEY: None,
        AUTENTICADO_SESSION_KEY: False,
        PAGINA_ATUAL_SESSION_KEY: 'login'
    }
    
    for key, default in required_keys.items():
        if key not in st.session_state:
            st.session_state[key] = default

    # Controle de navegação
    if st.session_state[AUTENTICADO_SESSION_KEY]:
        st.switch_page("pages/projetos.py")  # Redirecionamento mais rápido
    else:
        pagina_login()