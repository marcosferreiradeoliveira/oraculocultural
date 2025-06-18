import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
from datetime import datetime
import time
from constants import PAGINA_ATUAL_SESSION_KEY, USER_SESSION_KEY, AUTENTICADO_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message

def pagina_cadastro():
    """
    Página de Cadastro de Usuário
    """
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase()
    if not firebase_app:
        st.error(get_error_message())
        return

    # --- CSS Styles para layout consistente com login ---
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
        .cadastro-left-panel {
            background: linear-gradient(120deg, #e9d5ff, #f3e8ff, #faf5ff) !important;
            display: flex; flex-direction: column; justify-content: center;
            padding: 2rem 3rem; color: #1e293b; height: 100%;
        }
        .cadastro-left-panel h1 { 
            font-family: 'Playfair Display', serif;
            font-size: 3.5rem; 
            font-weight: 700; 
            margin-bottom: 1.5rem; 
            color: #1e293b; 
        }
        .cadastro-left-panel .subtitle { 
            font-family: 'Playfair Display', serif;
            font-size: 1.5rem; 
            font-weight: 500; 
            margin-bottom: 1.5rem; 
            color: #334155; 
        }
        .cadastro-left-panel .description { 
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
        .cadastro-right-panel {
            background-color: white !important;
            display: flex; flex-direction: column;
            justify-content: center; align-items: center;
            padding: 2rem !important;
            box-shadow: -10px 0 15px -3px rgba(0,0,0,0.1) !important;
            height: 100%; border-radius: 2rem !important;
            text-align: center !important;
        }
        .cadastro-right-panel > *:first-child {
            margin-top: 0 !important;
        }
        .cadastro-right-panel img {
            margin: 0 auto 2rem auto !important;
            background: transparent !important;
            display: block !important;
        }
        .cadastro-right-panel div[data-testid="stImage"] {
            margin: 0 auto 2rem auto !important;
            padding: 0 !important;
            display: block !important;
        }
        .cadastro-right-panel .logo { 
            margin: 0 auto 2rem auto !important; 
            width: 80px; 
            height: 80px; 
            display: block !important;
        }
        .cadastro-right-panel h2 { 
            font-family: 'Playfair Display', serif;
            font-size: 2rem; 
            font-weight: 700; 
            color: #1e293b; 
            margin: 0 auto 0.5rem auto !important; 
            text-align: center !important; 
        }
        .cadastro-right-panel .subtitle { 
            font-size: 1rem; 
            color: #64748b; 
            margin: 0 auto 2.5rem auto !important; 
            text-align: center !important; 
        }
        .cadastro-form {
            width: 100% !important;
            max-width: 400px !important;
            margin: 0 auto !important;
        }
        .cadastro-form .field-label { font-size: 0.9rem; font-weight: 500; color: #334155; margin-bottom: 0.5rem; }
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
        .back-to-login-button button {
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
        .back-to-login-button button:hover { 
            background-color: #f3e8ff !important;
            text-decoration: underline !important; 
        }
        .back-to-login-container {
            text-align: center; width: 100%; max-width: 400px;
            margin-top: 1rem; margin-bottom: 1.5rem;
        }
        
        @media (max-width: 992px) {
            .cadastro-master-container { flex-direction: column; height: auto; }
            .cadastro-left-panel { padding: 2rem; }
            .cadastro-left-panel h1 { font-size: 2.5rem; }
            .cadastro-right-panel { border-radius: 2rem 2rem 0 0; padding-top: 3rem; }
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
        .cadastro-left-panel, .cadastro-right-panel {
            padding-bottom: 5rem !important;
        }
        
        /* CSS específico para o layout de vídeo */
        .cadastro-left-panel {
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }
        .cadastro-content {
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

    # --- Layout Principal ---
    col_esquerda, col_direita = st.columns([0.55, 0.45])

    with col_esquerda:
        st.markdown("""
            <div class="cadastro-left-panel">
                <div class="cadastro-content">
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

    with col_direita:
        st.markdown("""
            <div class="cadastro-right-panel">
                <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" class="logo" alt="Oráculo Cultural Logo">
                <h2>Crie sua conta</h2>
                <p class="subtitle">Junte-se ao Oráculo Cultural</p>
            </div>
        """, unsafe_allow_html=True)

        # Formulário de cadastro
        with st.form("cadastro_form", clear_on_submit=False):
            st.markdown('<p class="field-label">Nome Completo</p>', unsafe_allow_html=True)
            nome_completo = st.text_input("Nome Completo", placeholder="Seu nome completo", key="cadastro_nome", label_visibility="collapsed")

            st.markdown('<p class="field-label">E-mail</p>', unsafe_allow_html=True)
            email = st.text_input("Email", placeholder="seu@email.com", key="cadastro_email", label_visibility="collapsed")

            st.markdown('<p class="field-label">Senha</p>', unsafe_allow_html=True)
            senha = st.text_input("Senha", type="password", placeholder="••••••••", key="cadastro_senha", label_visibility="collapsed")

            st.markdown('<p class="field-label">Confirmar Senha</p>', unsafe_allow_html=True)
            confirmar_senha = st.text_input("Confirmar Senha", type="password", placeholder="••••••••", key="cadastro_confirmar_senha", label_visibility="collapsed")

            submitted = st.form_submit_button("Cadastrar", use_container_width=True)
            if submitted:
                if senha != confirmar_senha:
                    st.error("As senhas não coincidem")
                    return
                try:
                    user = auth.create_user(
                        email=email,
                        password=senha,
                        display_name=nome_completo
                    )
                    user_data = {
                        'uid': user.uid,
                        'email': email,
                        'nome_completo': nome_completo,
                        'data_cadastro': firestore.SERVER_TIMESTAMP,
                        'ultimo_login': firestore.SERVER_TIMESTAMP
                    }
                    db = firestore.client()
                    db.collection('usuarios').document(user.uid).set(user_data)
                    st.session_state[USER_SESSION_KEY] = {
                        'uid': user.uid,
                        'email': email,
                        'display_name': nome_completo
                    }
                    st.session_state[AUTENTICADO_SESSION_KEY] = True
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                    st.success("Cadastro realizado com sucesso!")
                    st.rerun()
                except auth.EmailAlreadyExistsError:
                    st.error("Este email já está cadastrado")
                except Exception as e:
                    st.error(f"Erro ao cadastrar: {str(e)}")
                    try:
                        if 'user' in locals():
                            auth.delete_user(user.uid)
                    except:
                        pass

        # Trocar o botão de voltar para login por um link
        st.markdown('<div class="back-to-login-container" style="text-align:center;">', unsafe_allow_html=True)
        if st.button("Já tem conta? Vá para a página de login", key="go_to_login_btn", type="secondary"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
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