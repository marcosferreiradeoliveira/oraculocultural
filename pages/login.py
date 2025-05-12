import streamlit as st
from firebase_admin import auth

def pagina_login():
    # Conteúdo q   with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            st.image("assets/logo_edital_vale.jpg", width=300)
            
            st.title("Acesso ao Oráculo Cultural")
            st.markdown("""
                <style>
                    .login-box {
                        background-color: #f8f9fa;
                        padding: 2rem;
                        border-radius: 10px;
                        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
                    }
                    .title {
                        color: #2c3e50;
                        text-align: center;
                        margin-bottom: 1.5rem;
                    }
                </style>
                <div class="login-box">
                    <h3 class="title">Edital Instituto Cultural Vale 2025</h3>
            """, unsafe_allow_html=True)
            
            # Formulário de login
            with st.form("login_form"):
                email = st.text_input("E-mail", placeholder="seu@email.com")
                password = st.text_input("Senha", type="password", placeholder="••••••••")
                
                if st.form_submit_button("Entrar", use_container_width=True):
                    try:
                        user = auth.get_user_by_email(email)
                        st.session_state.update({
                            'user': {'email': email, 'uid': user.uid},
                            'autenticado': True
                        })
                        st.rerun()
                    except Exception as e:
                        st.error(f"Credenciais inválidas. Por favor, tente novamente.")
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown("""
                <div style="text-align: center; margin-top: 2rem; color: #7f8c8d;">
                    <p>Em caso de problemas, contate: <a href="mailto:edital@institutoculturalvale.org">edital@institutoculturalvale.org</a></p>
                </div>
            """, unsafe_allow_html=True)

