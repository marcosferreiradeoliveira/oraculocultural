import streamlit as st
import firebase_admin
from firebase_admin import auth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from constants import PAGINA_ATUAL_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message
from services.env_manager import get_env_value

@st.cache_resource
def initialize_firebase_app():
    """Inicializa o Firebase com cache para melhor performance"""
    if not initialize_firebase():
        st.error(get_error_message())
        return False
    return True

def send_reset_email(email, reset_link):
    """Envia email com link de reset de senha"""
    try:
        # Configurações do email do ambiente Railway
        sender_email = get_env_value("email.user")
        sender_password = get_env_value("email.password")
        
        if not sender_email or not sender_password:
            st.error("Configurações de email não encontradas. Por favor, configure as credenciais de email no Railway.")
            return False
        
        # Criar mensagem
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = email
        msg['Subject'] = "Redefinição de Senha - Oráculo Cultural"
        
        # Corpo do email
        body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #7e22ce;">Redefinição de Senha</h2>
                    <p>Olá,</p>
                    <p>Recebemos uma solicitação para redefinir sua senha no Oráculo Cultural.</p>
                    <p>Clique no botão abaixo para criar uma nova senha:</p>
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" style="background-color: #7e22ce; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">Redefinir Senha</a>
                    </div>
                    <p>Se você não solicitou esta redefinição, por favor ignore este email.</p>
                    <p>Este link é válido por 1 hora.</p>
                    <p>Atenciosamente,<br>Equipe Oráculo Cultural</p>
                </div>
            </body>
        </html>
        """
        
        msg.attach(MIMEText(body, 'html'))
        
        # Configurar servidor SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        
        # Enviar email
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        st.error(f"Erro ao enviar email: {str(e)}")
        return False

def pagina_reset_password():
    """Exibe a página de reset de senha"""
    # Inicializa o Firebase
    firebase_app = initialize_firebase_app()
    if not firebase_app:
        return

    st.markdown("""
    <style>
        .reset-container {
            max-width: 500px;
            margin: 0 auto;
            padding: 2rem;
            background-color: white;
            border-radius: 1rem;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);
        }
        .reset-title {
            color: #1e293b;
            font-size: 1.5rem;
            font-weight: 600;
            margin-bottom: 1rem;
            text-align: center;
        }
        .reset-subtitle {
            color: #64748b;
            font-size: 1rem;
            margin-bottom: 2rem;
            text-align: center;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="reset-container">', unsafe_allow_html=True)
    st.markdown('<h2 class="reset-title">Esqueceu sua senha?</h2>', unsafe_allow_html=True)
    st.markdown('<p class="reset-subtitle">Digite seu email para receber um link de redefinição de senha.</p>', unsafe_allow_html=True)

    with st.form("reset_password_form"):
        email = st.text_input("Email", placeholder="seu@email.com")
        submit = st.form_submit_button("Enviar Link de Redefinição")

        if submit:
            if not email:
                st.error("Por favor, insira seu email.")
            else:
                try:
                    # Gerar link de reset de senha
                    reset_link = auth.generate_password_reset_link(email)
                    
                    # Enviar email com o link
                    if send_reset_email(email, reset_link):
                        st.success("Link de redefinição de senha enviado com sucesso! Verifique seu email.")
                        st.info("O link é válido por 1 hora.")
                        # Aguarda 2 segundos antes de redirecionar
                        import time
                        time.sleep(2)
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
                        st.rerun()
                    else:
                        st.error("Não foi possível enviar o email. Por favor, tente novamente mais tarde.")
                
                except auth.UserNotFoundError:
                    st.error("Email não encontrado. Verifique se o email está correto.")
                except Exception as e:
                    st.error(f"Erro ao processar a solicitação: {str(e)}")

    # Botão para voltar ao login
    if st.button("⬅️ Voltar para Login"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

if __name__ == '__main__':
    pagina_reset_password()