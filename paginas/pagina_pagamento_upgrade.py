import streamlit as st
from constants import PAGINA_ATUAL_SESSION_KEY, USER_SESSION_KEY # Adicionar USER_SESSION_KEY
import mercadopago
import os # Para carregar variáveis de ambiente
import uuid # Para gerar IDs únicos se necessário

# Função para obter a URL base da aplicação (ajuste conforme necessário)
def get_base_url():
    # 1. Tentar obter de st.secrets (para produção no Streamlit Cloud)
    if hasattr(st, 'secrets'):
        # Verifica se a chave está diretamente em secrets ou aninhada
        if "STREAMLIT_BASE_URL" in st.secrets:
            base_url_from_secrets = st.secrets.get("STREAMLIT_BASE_URL")
            if base_url_from_secrets:
                return base_url_from_secrets
        # Verifica se está aninhada sob [mercadopago] como no seu exemplo
        elif "mercadopago" in st.secrets and "STREAMLIT_BASE_URL" in st.secrets.mercadopago:
            base_url_from_secrets = st.secrets.mercadopago.get("STREAMLIT_BASE_URL")
            if base_url_from_secrets:
                return base_url_from_secrets
    # 2. Tentar obter de variável de ambiente (para outros cenários de deploy ou local)
    return os.getenv("STREAMLIT_BASE_URL", "http://localhost:8501")

def pagina_pagamento_upgrade():
    """
    Página de Upgrade de Plano
    """
    st.title("🚀 Upgrade para o Plano Premium")
    st.markdown("Desbloqueie todos os recursos e eleve seus projetos culturais ao próximo nível!")

    # Informações para ambiente de teste
    if os.getenv("MP_ACCESS_TOKEN", "").startswith("TEST-"):
        st.info("""
        🔍 **Modo de Teste Ativo**
        
        Para testar o pagamento, use estas credenciais:
        - Email: TESTUSER973178250
        - Senha: ZmCuO5A5sm
        
        Este é um ambiente de teste. Nenhum valor real será cobrado.
        """)

    # Recuperar informações do usuário para o external_reference
    user_info = st.session_state.get(USER_SESSION_KEY)
    if not user_info or not user_info.get('uid'):
        st.error("Erro: Usuário não identificado. Por favor, faça login novamente.")
        if st.button("Ir para Login"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()
        return
    user_uid = user_info.get('uid')

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
        ### **Valor: R$ 249,00 / mês**
        """
    )

    if st.button("💳 Pagar com Mercado Pago e Ativar Premium", type="primary", use_container_width=True):
        # Carregar Access Token do Mercado Pago (de st.secrets ou .env)
        try:
            mp_access_token = None
            
            # 1. Tentar carregar do .env primeiro (ideal para desenvolvimento local)
            if os.path.exists(".env"):
                mp_access_token = os.getenv("MP_ACCESS_TOKEN")
                print(f"DEBUG: MP_ACCESS_TOKEN from .env: {'Found' if mp_access_token else 'Not found'}")

            # 2. Se não encontrou no .env, tentar carregar de st.secrets (para produção)
            if not mp_access_token:
                if hasattr(st, 'secrets'):
                    mercadopago_secrets = st.secrets.get("mercadopago", {})
                    mp_access_token = mercadopago_secrets.get("access_token")
                    print(f"DEBUG: MP_ACCESS_TOKEN from st.secrets: {'Found' if mp_access_token else 'Not found'}")
                else:
                    print("DEBUG: st.secrets not available")
            
            if not mp_access_token:
                st.error("Credenciais do Mercado Pago não configuradas. Por favor, configure MP_ACCESS_TOKEN no arquivo .env (desenvolvimento) ou em st.secrets (produção).")
                return

            # Validate token format before using
            if not mp_access_token.startswith('TEST-') and not mp_access_token.startswith('APP_USR-'):
                st.error("Token do Mercado Pago inválido. O token deve começar com 'TEST-' (ambiente de teste) ou 'APP_USR-' (produção).")
                return

            sdk = mercadopago.SDK(mp_access_token)

            base_url = get_base_url()
            preference_id = str(uuid.uuid4())

            # Ensure base_url doesn't end with a slash
            base_url = base_url.rstrip('/')

            # Dados da preferência de pagamento
            preference_data = {
                "items": [
                    {
                        "id": "premium_plan_monthly_01",
                        "title": "Plano Premium Mensal - Oráculo Cultural",
                        "quantity": 1,
                        "currency_id": "BRL",
                        "unit_price": 249.00
                    }
                ],
                "back_urls": {
                    "success": f"{base_url}?page=payment_success",
                    "failure": f"{base_url}?page=payment_failure",
                    "pending": f"{base_url}?page=payment_pending"
                },
                "auto_return": "approved",  # Adicionado este parâmetro
                "external_reference": user_uid,
                "notification_url": f"{base_url}/mercadopago_webhook",
                "statement_descriptor": "ORACULO PREMIUM",
                "metadata": {
                    "user_uid": user_uid,
                    "plan_id": "premium_monthly",
                    "preference_id": preference_id
                }
            }

            preference_response = sdk.preference().create(preference_data)
            preference = preference_response["response"]

            if preference_response["status"] == 201:
                init_point = preference["init_point"]
                st.session_state['mp_preference_id'] = preference["id"] # Salva o ID da preferência real do MP
                st.info("Você será redirecionado para o Mercado Pago para concluir o pagamento...")
                # Usar st.components.v1.html para um redirecionamento mais robusto ou meta refresh
                st.markdown(f'<meta http-equiv="refresh" content="3; url={init_point}">', unsafe_allow_html=True)
                st.markdown(f"Se não for redirecionado automaticamente, [clique aqui para pagar]({init_point}).")
            else:
                st.error(f"Erro ao criar preferência de pagamento: {preference_response.get('response', {}).get('message', 'Erro desconhecido')}")
                st.json(preference_response) # Para depuração

        except Exception as e:
            st.error(f"Ocorreu um erro ao processar o pagamento: {str(e)}")

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
