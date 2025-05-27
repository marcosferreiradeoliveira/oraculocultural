import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
from constants import PAGINA_ATUAL_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message

def pagina_cadastro():
    """Exibe a página de cadastro com layout moderno e otimizado"""
    # Inicializa o Firebase e obtém o cliente Firestore
    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                st.error(get_error_message())
                return
        db = firestore.client()
    except Exception as e:
        if "already initialized" not in str(e).lower(): # Ignora erro de já inicializado
            st.error(f"Falha ao inicializar Firebase Admin (necessário para Firestore): {e}")
            print(f"Erro de inicialização Firebase em pagina_cadastro: {e}")
            return
        try:
            db = firestore.client()
        except Exception as e:
            st.error(f"Erro ao obter cliente Firestore: {e}")
            return

    # CSS Styles
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
            padding: 2rem !important;
            box-shadow: -10px 0 15px -3px rgba(0,0,0,0.1) !important;
            height: 100%; border-radius: 2rem !important;
            text-align: center !important;
        }
        .login-right-panel > *:first-child {
            margin-top: 0 !important;
        }
        .login-right-panel img {
            margin: 0 auto 2rem auto !important;
            background: transparent !important;
            display: block !important;
        }
        .login-right-panel div[data-testid="stImage"] {
            margin: 0 auto 2rem auto !important;
            padding: 0 !important;
            display: block !important;
        }
        .login-right-panel .logo { 
            margin: 0 auto 2rem auto !important; 
            width: 80px; 
            height: 80px; 
            display: block !important;
        }
        .login-right-panel h2 { 
            font-family: 'Playfair Display', serif;
            font-size: 2rem; 
            font-weight: 700; 
            color: #1e293b; 
            margin: 0 auto 0.5rem auto !important; 
            text-align: center !important; 
        }
        .login-right-panel .subtitle { 
            font-size: 1rem; 
            color: #64748b; 
            margin: 0 auto 2.5rem auto !important; 
            text-align: center !important; 
        }
        .login-form {
            width: 100% !important;
            max-width: 400px !important;
            margin: 0 auto !important;
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
    </style>
    """, unsafe_allow_html=True)

    # Layout Principal
    st.markdown('<div class="login-master-container">', unsafe_allow_html=True)
    
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
            </div>
        """, unsafe_allow_html=True)

    with col_direita:
        st.markdown("""
            <div class="login-right-panel">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" class="logo" alt="Oráculo Cultural Logo">
                <h2>Cadastre-se</h2>
                <p class="subtitle">Preencha os campos abaixo para criar sua conta</p>
            </div>
        """, unsafe_allow_html=True)

        # Formulário de cadastro
        with st.form("cadastro_form_main", clear_on_submit=False):
            st.markdown('<p class="field-label">Nome Completo</p>', unsafe_allow_html=True)
            nome_completo = st.text_input("Nome Completo", placeholder="Seu nome completo", key="cadastro_nome", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">E-mail</p>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="seu@email.com", key="cadastro_email", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Senha</p>', unsafe_allow_html=True)
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="cadastro_senha", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Confirme sua Senha</p>', unsafe_allow_html=True)
            confirmar_senha = st.text_input("Confirme sua Senha", type="password", placeholder="••••••••", key="cadastro_confirmar_senha", label_visibility="collapsed")
            
            st.markdown('<p class="field-label">Nome da Empresa (Opcional)</p>', unsafe_allow_html=True)
            empresa = st.text_input("Nome da Empresa", placeholder="Nome da sua empresa", key="cadastro_empresa", label_visibility="collapsed")
            
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
            
            cadastro_submit = st.form_submit_button("Criar Conta", use_container_width=True)
            
            if cadastro_submit:
                with st.spinner("Criando sua conta..."):
                    if handle_cadastro(nome_completo, email, senha, confirmar_senha, empresa):
                        st.rerun()

        # Link para voltar ao login
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
        
        st.markdown('<div class="signup-link">', unsafe_allow_html=True)
        if st.button("Já tem uma conta? Faça login", key="login_button", type="secondary", use_container_width=True):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)