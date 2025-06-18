import streamlit as st
from constants import PAGINA_ATUAL_SESSION_KEY, USER_SESSION_KEY
import mercadopago
import os
import uuid
import firebase_admin
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter
import time
from services.firebase_init import initialize_firebase, get_error_message
from constants import AUTENTICADO_SESSION_KEY
from utils.analytics import track_event, track_page_view
from services.env_manager import get_env_value

# Função para obter a URL base da aplicação
def get_base_url():
    base_url = get_env_value("mercadopago.STREAMLIT_BASE_URL")
    if base_url:
        return base_url.rstrip('/')
    return os.getenv("STREAMLIT_BASE_URL", "https://oraculocultural.streamlit.app").rstrip('/')

def get_mercadopago_credentials():
    """
    Obtém as credenciais do Mercado Pago do ambiente Railway
    """
    return {
        'access_token': get_env_value("mercadopago.access_token"),
        'public_key': get_env_value("mercadopago.public_key")
    }

def pagina_pagamento_upgrade():
    """
    Página de Upgrade de Plano
    """
    # Track page view
    track_page_view('Upgrade Payment Page')
    
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase()
    if not firebase_app:
        st.error(get_error_message())
        return

    if not st.session_state.get(USER_SESSION_KEY):
        st.warning("Usuário não logado.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

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

    # Debug: verificar credenciais
    print(f"DEBUG: MP Access Token presente: {bool(mp_access_token)}")
    print(f"DEBUG: MP Public Key presente: {bool(mp_public_key)}")
    if mp_access_token:
        print(f"DEBUG: MP Access Token (primeiros 10 chars): {mp_access_token[:10]}...")

    if not mp_access_token:
        st.error("Credenciais do Mercado Pago não configuradas")
        st.write("Verifique se as variáveis de ambiente MP_ACCESS_TOKEN estão configuradas no arquivo .env")
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
        track_event('upgrade_click')
        try:
            start_time = time.time()
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
                    "success": f"{base_url}/?page=payment_success",
                    "failure": f"{base_url}/?page=payment_failure",
                    "pending": f"{base_url}/?page=payment_pending"
                },
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

                # Track successful upgrade
                end_time = time.time()
                processing_time = end_time - start_time
                
                track_event('upgrade_success', {
                    'processing_time': processing_time,
                    'user_email': payer_email
                })
            else:
                st.error(f"Erro ao criar preferência de pagamento. Status: {preference_response['status']}")
                st.write("Resposta completa do Mercado Pago:")
                st.json(preference_response)
                st.write("Verifique se as credenciais do Mercado Pago estão configuradas corretamente e se o e-mail do usuário é válido.")

        except Exception as e:
            track_event('upgrade_failed', {
                'error_message': str(e)
            })
            st.error(f"Ocorreu um erro ao processar o pagamento: {str(e)}")
            st.write("Verifique se as credenciais do Mercado Pago estão configuradas corretamente.")

    # Botão para voltar para a página de perfil
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()

# Adicione estas funções ao final do arquivo

def pagina_payment_success():
    st.title("🎉 Pagamento Aprovado!")
    
    # Recuperar informações do usuário
    user_info = st.session_state.get(USER_SESSION_KEY)
    if not user_info or not user_info.get('uid'):
        st.error("Erro: Usuário não identificado. Por favor, faça login novamente.")
        if st.button("Ir para Login"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
        return

    user_uid = user_info.get('uid')
    
    # Atualizar status premium no Firestore
    try:
        db = firestore.client()
        user_ref = db.collection('usuarios').document(user_uid)
        
        # Atualizar o status premium e adicionar data de ativação
        user_ref.update({
            'premium': True,
            'data_ativacao_premium': firestore.SERVER_TIMESTAMP,
            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
        })
        
        st.success("Seu acesso Premium foi ativado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao ativar acesso Premium: {str(e)}")
        return

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
