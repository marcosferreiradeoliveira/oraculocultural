import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth
import os
import time
from services.firebase_init import initialize_firebase, get_error_message
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY # Importado de constants

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
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos' # Destino padrão, será reavaliado em app.py
        st.session_state['just_logged_in'] = True # Nova flag para indicar login recente
        
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
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        html, body {
            padding: 0 !important;
            margin: 0 !important;
            height: 100% !important;
            overflow: hidden !important;
            background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff) !important;
            font-family: 'Poppins', sans-serif;
        }

        .stApp > header { display: none !important; }
        section.main.main { 
            padding-top: 0 !important; margin-top: 0 !important; 
            background-color: transparent !important;
        }
        .stApp section.main.main > div[data-testid="stVerticalBlock"] > div[data-testid="stVerticalBlockBorderWrapper"] > div > div[data-testid="block-container"]:first-child {
            padding: 0 !important; margin: 0 !important;
            height: 100vh !important;
            background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff) !important;
            display: flex !important;
            flex-direction: row !important;
        }
        .login-left-panel {
            background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff) !important;
            display: flex; flex-direction: column; justify-content: center;
            padding: 2rem 3rem; color: #1e293b; height: 100%;
        }
        .login-left-panel h1 { 
            font-family: 'Playfair Display', serif;
            font-size: 3.5rem; 
            font-weight: 700; 
            margin-bottom: 1.5rem; 
            color: #1e293b; 
        }
        .login-left-panel .subtitle { 
            font-family: 'Playfair Display', serif;
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
        .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 2rem; }
        .stat-card {
            background-color: white; border-radius: 1rem; padding: 1.5rem 1rem; text-align: center;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
            display: flex; align-items: center; gap: 1rem;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
            font-family: 'Poppins', sans-serif;
        }
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px -1px rgba(0,0,0,0.15), 0 3px 6px -1px rgba(0,0,0,0.1);
        }
        .stat-icon {
            font-size: 1.5rem;
            color: #7e22ce;
            flex-shrink: 0;
        }
        .stat-label { 
            font-size: 1rem; 
            color: #334155;
            font-weight: 500;
            text-align: left;
            flex-grow: 1;
            font-family: 'Poppins', sans-serif;
        }
        .login-right-panel {
            background-color: white !important;
            display: flex; flex-direction: column;
            justify-content: center; align-items: center;
            padding: 0 2rem 2rem 2rem !important;
            box-shadow: -10px 0 15px -3px rgba(0,0,0,0.1) !important;
            height: 100%; border-radius: 2rem 0 0 2rem !important;
        }
        .login-right-panel > *:first-child {
            margin-top: 0 !important;
        }
        .login-right-panel img {
            margin-bottom: 2rem;
            background: transparent !important;
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        /* Target the container element generated by Streamlit for the image */
        .login-right-panel div[data-testid="stImage"] {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        .login-right-panel .logo { margin-bottom: 2rem; width: 80px; height: 80px; }
        .login-right-panel h2 { 
            font-family: 'Playfair Display', serif;
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
        .login-form .field-label { font-size: 0.9rem; font-weight: 500; color: #334155; margin-bottom: 0.5rem; }
        .stButton button {
            font-family: 'Poppins', sans-serif;
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
        .forgot-password-button button {
            font-family: 'Poppins', sans-serif;
            background-color: white !important; 
            color: #7e22ce !important;
            border: 1px solid #7e22ce !important; 
            padding: 0 !important;
            font-size: 0.875rem !important; 
            font-weight: normal !important;
            text-decoration: none !important; 
            width: auto !important; 
            display: inline !important;
        }
        .forgot-password-button button:hover { 
            background-color: #f3e8ff !important;
            text-decoration: underline !important; 
        }
        .forgot-password-container {
            text-align: right; width: 100%; max-width: 400px;
            margin-top: -1rem; margin-bottom: 1.5rem;
        }
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
        
        div.signup-link div[data-testid="stButton"] button {
            font-family: 'Poppins', sans-serif;
            background-color: white !important;
            color: #7e22ce !important;
            border: 1px solid #7e22ce !important;
            padding: 0.5rem 1rem !important;
            font-size: 0.875rem !important;
            font-weight: normal !important;
            text-decoration: none !important;
            width: auto !important;
            display: inline !important;
            box-shadow: none !important;
            line-height: inherit !important;
        }

        div.signup-link div[data-testid="stButton"] button:hover {
            background-color: #f3e8ff !important;
            text-decoration: underline !important;
        }
        
        @media (max-width: 992px) {
            .login-master-container { flex-direction: column; height: auto; }
            .login-left-panel { padding: 2rem; }
            .login-left-panel h1 { font-size: 2.5rem; }
            .login-right-panel { border-radius: 2rem 2rem 0 0; padding-top: 3rem; }
            .stats-grid { grid-template-columns: repeat(1, 1fr); }
        }

        /* Adicionar CSS para o rodapé */
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background-color: white;
            padding: 1rem 0;
            box-shadow: 0 -2px 10px rgba(0,0,0,0.05);
            font-family: 'Poppins', sans-serif;
        }
        .footer-content {
            max-width: 1200px;
            margin: 0 auto;
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0 2rem;
        }
        .footer-left {
            display: flex;
            align-items: center;
            gap: 1rem;
        }
        .footer-logo {
            height: 30px;
            width: auto;
        }
        .footer-right {
            display: flex;
            gap: 2rem;
        }
        .footer-link {
            color: #64748b;
            text-decoration: none;
            font-size: 0.875rem;
            transition: color 0.2s ease;
        }
        .footer-link:hover {
            color: #7e22ce;
        }
        .footer-copyright {
            color: #64748b;
            font-size: 0.875rem;
        }

        /* Ajustar o padding do conteúdo principal para não sobrepor o rodapé */
        .login-left-panel, .login-right-panel {
            padding-bottom: 5rem !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # --- Layout Principal (mantido igual) ---
    # st.markdown('<div class="login-master-container">', unsafe_allow_html=True)
    
    col_esquerda, col_direita = st.columns([0.55, 0.45])

    with col_esquerda:
        st.markdown("""
            <div class="login-left-panel">
                <div class="login-content">
                    <h1>Oráculo Cultural</h1>
                    <p class="subtitle">Sua plataforma para decifrar o universo da cultura</p>
                    <p class="description">Descubra, conecte-se e explore o mundo cultural através de uma experiência única e personalizada.</p>
                    <div class="stats-grid">
                        <div class="stat-card">
                            <div class="stat-icon">🔍</div>
                            <div class="stat-label">Diagnóstico do seu projeto</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">📊</div>
                            <div class="stat-label">Comparação com últimos selecionados</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-icon">📝</div>
                            <div class="stat-label">Geração de documentos customizada</div>
                        </div>
                    </div>
                </div>
                <div class="video-container">
                    <iframe 
                        src="https://www.youtube.com/embed/3CIJYnVlJO8"
                        frameborder="0"
                        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                        allowfullscreen>
                    </iframe>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Adicionar CSS específico para o novo layout
        st.markdown("""
        <style>
            .login-left-panel {
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }
            .login-content {
                flex: 0 0 auto;
            }
            .video-container {
                flex: 0 0 auto;
                position: relative;
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                padding-bottom: 56.25%;
            }
            .video-container iframe {
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
            }
        </style>
        """, unsafe_allow_html=True)

    with col_direita:
        st.markdown("""
            <div class="login-right-panel">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" class="logo" alt="Oráculo Cultural Logo">
                <h2>Bem-vindo ao Oráculo Cultural</h2>
                <p class="subtitle">Aproveite o trial de um dia para experimentar a ferramenta à vontade</p>
            </div>
        """, unsafe_allow_html=True)

        # Formulário de login otimizado
        with st.form("login_form_main", clear_on_submit=False):
            st.markdown('<p class="field-label">E-mail</p>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="seu@email.com", key="login_email", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Senha</p>', unsafe_allow_html=True)
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="login_senha", label_visibility="collapsed")
            
            st.checkbox("Lembrar-me", key="login_remember")
            
            st.markdown("""
            <style>
                div[data-testid="stForm"] button[type="submit"] {
                    background-color: #7e22ce !important;
                    color: white !important;
                    border: none !important;
                    width: 100% !important;
                    padding: 0.75rem 1rem !important;
                    font-weight: 600 !important;
                    font-family: 'Poppins', sans-serif !important;
                }
                div[data-testid="stForm"] button[type="submit"]:hover {
                    background-color: #6b21a8 !important;
                }
                div[data-testid="stForm"] button[type="submit"]:focus {
                    background-color: #7e22ce !important;
                    box-shadow: none !important;
                }
                div[data-testid="stForm"] button[type="submit"]:active {
                    background-color: #6b21a8 !important;
                }
            </style>
            """, unsafe_allow_html=True)
            
            login_submit = st.form_submit_button("Entrar", use_container_width=True)
            
            if login_submit:
                with st.spinner("Autenticando..."):
                    if handle_login(email, senha):
                        st.rerun()

        # Link para reset de senha
        st.markdown("""
        <style>
            div[data-testid="stButton"] button[kind="secondary"] {
                background-color: white !important;
                color: #7e22ce !important;
                border: 1px solid #7e22ce !important;
            }
            div[data-testid="stButton"] button[kind="secondary"]:hover {
                background-color: #f3e8ff !important;
            }
        </style>
        """, unsafe_allow_html=True)
        
        st.markdown('<div class="forgot-password-container">', unsafe_allow_html=True)
        if st.button("Esqueci minha senha", key="forgot_password_btn", type="secondary"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'reset_password'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Link de cadastro
        st.markdown('<div class="signup-link">', unsafe_allow_html=True)
        if st.button("Novo por aqui? Cadastre-se", key="signup_button", type="secondary"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'cadastro'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Adicionar o rodapé
    st.markdown("""
    <div class="footer">
        <div class="footer-content">
            <div class="footer-left">
                <a href="https://www.mobcontent.com.br" target="_blank" style="text-decoration: none; display: flex; align-items: center; gap: 1rem;">
                    <img src="https://mobcontent.com.br/wp-content/uploads/2021/04/cropped-cropped-favicon-mobcontent-2-1.png" alt="MobContent Logo" class="footer-logo">
                    <span class="footer-copyright">Um produto MobContent</span>
                </a>
                <span class="footer-copyright" style="margin-left: 1rem;">•</span>
                <span class="footer-copyright">Todos os direitos reservados</span>
            </div>
            <div class="footer-right">
                <a href="#" class="footer-link">Política de privacidade</a>
                <a href="#" class="footer-link">Contato</a>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

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