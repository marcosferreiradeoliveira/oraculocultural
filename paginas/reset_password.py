import streamlit as st
import firebase_admin
from firebase_admin import auth
from constants import PAGINA_ATUAL_SESSION_KEY
import time

def pagina_reset_password():
    """Página para recuperação de senha"""

    st.markdown("""
        <style>
            .reset-container {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            
            .reset-title {
                color: #1e293b;
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 1rem;
                text-align: center;
            }
            
            .reset-description {
                color: #64748b;
                margin-bottom: 2rem;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)
    
    # Exibe o formulário de recuperação de senha
    with st.container():
        st.markdown("""
            <div class="reset-container">
                <div style="text-align:center; margin-bottom: 1.5rem;">
                    <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" alt="Oráculo Cultural Logo" style="width:80px;height:80px;"/>
                </div>
                <h2 class="reset-title">Recuperar Senha</h2>
                <p class="reset-description">Digite seu email para receber um link de recuperação de senha.</p>
            </div>
        """, unsafe_allow_html=True)
    
    with st.form("reset_password_form"):
        email = st.text_input("Email", placeholder="seu@email.com")
        submitted = st.form_submit_button("Enviar Link de Recuperação")
        
        if submitted:
            if email:
                try:
                    # Gera e envia o link de recuperação de senha usando Firebase Auth
                    auth.generate_password_reset_link(email)
                    st.success("Email de recuperação enviado! Verifique sua caixa de entrada e spam.")
                    time.sleep(2)
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
                    st.rerun()
                except firebase_admin.auth.UserNotFoundError:
                    st.error("Nenhum usuário encontrado com este endereço de e-mail.")
                except Exception as e:
                    st.error(f"Erro ao enviar email de recuperação: {str(e)}")
            else:
                st.error("Por favor, digite um email válido.")
    
    # Botão para voltar ao login
    if st.button("⬅️ Voltar para Login", key="back_to_login_initial_reset_page"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()