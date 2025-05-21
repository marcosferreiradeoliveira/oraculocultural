import streamlit as st
from constants import PAGINA_ATUAL_SESSION_KEY, USER_SESSION_KEY
import mercadopago
import os
import uuid

# Função para obter a URL base da aplicação
def get_base_url():
    if hasattr(st, 'secrets'):
        if "mercadopago" in st.secrets and "STREAMLIT_BASE_URL" in st.secrets.mercadopago:
            base_url_from_secrets = st.secrets.mercadopago.get("STREAMLIT_BASE_URL")
            if base_url_from_secrets:
                return base_url_from_secrets.rstrip('/')
    return os.getenv("STREAMLIT_BASE_URL", "https://oraculocultural.streamlit.app").rstrip('/')

def get_mercadopago_credentials():
    """
    Obtém as credenciais do Mercado Pago, priorizando:
    1. Variáveis de ambiente (.env)
    2. st.secrets
    """
    credentials = {
        'access_token': None,
        'public_key': None
    }
    
    # Primeiro tenta carregar do .env
    if os.path.exists(".env"):
        from dotenv import load_dotenv
        load_dotenv()
        credentials['access_token'] = os.getenv("MP_ACCESS_TOKEN")
        credentials['public_key'] = os.getenv("MP_PUBLIC_KEY")
    
    # Se não encontrou no .env, tenta do st.secrets
    if not credentials['access_token'] and hasattr(st, 'secrets'):
        try:
            if "mercadopago" in st.secrets:
                mercadopago_content = st.secrets.mercadopago
                if hasattr(mercadopago_content, 'to_dict'):
                    mercadopago_content = mercadopago_content.to_dict()
                
                if isinstance(mercadopago_content, dict):
                    credentials['access_token'] = mercadopago_content.get('access_token')
                    credentials['public_key'] = mercadopago_content.get('public_key')
        except Exception as e:
            st.error("Erro ao carregar credenciais do Mercado Pago")
    
    return credentials

def pagina_pagamento_upgrade():
    """
    Página de Upgrade de Plano
    """
    st.title("🚀 Upgrade para o Plano Premium")
    
    # Botão de logout no topo
    if st.button("🚪 Fazer Logout", key="logout_top"):
        st.session_state.clear()
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()

    st.markdown("Desbloqueie todos os recursos e eleve seus projetos culturais ao próximo nível!")

    # Obter credenciais
    credentials = get_mercadopago_credentials()
    mp_access_token = credentials['access_token']
    mp_public_key = credentials['public_key']

    if not mp_access_token:
        st.error("Credenciais do Mercado Pago não configuradas")
        return

    # Recuperar informações do usuário
    user_info = st.session_state.get(USER_SESSION_KEY)
    if not user_info or not user_info.get('uid'):
        st.error("Erro: Usuário não identificado. Por favor, faça login novamente.")
        if st.button("Ir para Login"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
        return

    user_uid = user_info.get('uid')
    payer_email = user_info.get('email')

    # Detalhes do Plano
    st.subheader("Plano Premium Mensal")
    st.markdown(
        """
        - Criação **ilimitada** de projetos.
        - Acesso a **modelos de editais avançados**.
        - Ferramentas de **análise de viabilidade** detalhadas.
        - **Diagnóstico IA** mais completo para seus projetos.
        - **Geração de documentos** em múltiplos formatos.
        - **Suporte prioritário** e personalizado.
        ---
        ### **Valor: R$ 1,00 / mês**
        """
    )

    if st.button("💳 Pagar com Mercado Pago e Ativar Premium", type="primary", use_container_width=True):
        try:
            sdk = mercadopago.SDK(mp_access_token)
            base_url = get_base_url()
            preference_id = str(uuid.uuid4())

            preference_data = {
                "items": [
                    {
                        "id": "premium_plan_monthly_01",
                        "title": "Plano Premium Mensal - Oráculo Cultural (R$ 1,00)",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": 1.00
                    }
                ],
                "payer": {
                    "email": payer_email,
                    "entity_type": "individual"
                },
                "back_urls": {
                    "success": f"{base_url}?page=payment_success",
                    "failure": f"{base_url}?page=payment_failure",
                    "pending": f"{base_url}?page=payment_pending"
                },
                "auto_return": "approved",
                "external_reference": user_uid,
                "notification_url": f"{base_url}/mercadopago_webhook",
                "statement_descriptor": "ORACULO PREMIUM",
                "metadata": {
                    "user_uid": user_uid,
                    "plan_id": "premium_monthly",
                    "preference_id": preference_id,
                    "payer_email": payer_email,
                    "valor": 1.00
                }
            }

            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]

            if preference_response["status"] == 201:
                init_point = preference["init_point"]
                st.session_state['mp_preference_id'] = preference["id"]
                st.markdown(f'<meta http-equiv="refresh" content="3; url={init_point}">', unsafe_allow_html=True)
                st.markdown(f"Você será redirecionado para o Mercado Pago para concluir o pagamento... [Clique aqui se não for redirecionado automaticamente]({init_point}).")
            else:
                st.error("Erro ao criar preferência de pagamento")

        except Exception as e:
            st.error("Ocorreu um erro ao processar o pagamento")

    # Botão para voltar para a página de perfil
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()

# Adicione estas funções ao final do arquivo

def pagina_payment_success():
    st.title("🎉 Pagamento Aprovado!")
    st.success("Seu pagamento foi processado com sucesso. Seu acesso Premium será ativado em breve.")
    st.write("Obrigado por se juntar ao Oráculo Cultural Premium!")
    
    preference_id = st.query_params.get("pref_id", [None])[0]
    mp_payment_id = st.query_params.get("payment_id", [None])[0]
    mp_status = st.query_params.get("status", [None])[0]

    if preference_id:
        st.write(f"ID da Preferência da transação: {preference_id}")
    if mp_payment_id:
        st.write(f"ID do Pagamento no Mercado Pago: {mp_payment_id}")
    if mp_status:
        st.write(f"Status no Mercado Pago: {mp_status}")

    st.info("Importante: A ativação do plano pode levar alguns minutos enquanto processamos a confirmação final.")
    # Aqui, idealmente, você aguardaria a confirmação via webhook.
    # Para uma experiência de usuário imediata, você poderia verificar o status do pagamento
    # usando o mp_payment_id, mas o webhook é mais confiável.

    if st.button("Ir para Meus Projetos"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun()
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()

def pagina_payment_failure():
    st.title("❌ Falha no Pagamento")
    st.error("Houve um problema ao processar seu pagamento. Nenhuma cobrança foi realizada.")
    st.write("Por favor, tente novamente ou utilize outro método de pagamento, se disponível.")
    
    preference_id = st.query_params.get("pref_id", [None])[0]
    if preference_id:
        st.write(f"ID da Tentativa de transação: {preference_id}")

    if st.button("Tentar Novamente (Voltar para Upgrade)"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'pagamento_upgrade'
        st.rerun()
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()

def pagina_payment_pending():
    st.title("⏳ Pagamento Pendente")
    st.warning("Seu pagamento está pendente de processamento.")
    st.write("Isso pode acontecer com alguns métodos de pagamento como boleto bancário. Assim que o pagamento for confirmado, seu plano será ativado.")
    
    preference_id = st.query_params.get("pref_id", [None])[0]
    if preference_id:
        st.write(f"ID da transação: {preference_id}")

    st.info("Você receberá uma notificação quando o status do pagamento for atualizado.")
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()
