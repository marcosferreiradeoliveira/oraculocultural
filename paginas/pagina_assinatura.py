import streamlit as st
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter
from google.api_core.datetime_helpers import DatetimeWithNanoseconds as GCloudTimestamp
from constants import (
    USER_SESSION_KEY, 
    AUTENTICADO_SESSION_KEY, 
    PAGINA_ATUAL_SESSION_KEY
)
from datetime import datetime, timedelta, timezone

def pagina_assinatura():
    """
    Exibe a página de assinatura do usuário com informações sobre o plano atual,
    opções de upgrade e gerenciamento da assinatura.
    """
    if not st.session_state.get(AUTENTICADO_SESSION_KEY):
        st.warning("Você precisa estar logado para acessar esta página.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

    user_info = st.session_state.get(USER_SESSION_KEY)
    if not user_info:
        st.error("Não foi possível carregar as informações do usuário.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

    # Use columns to align title and buttons
    col_title, col_back, col_logout = st.columns([4, 1, 1])

    with col_title:
        st.markdown("## 💎 Assinatura")

    # Botão Voltar para Perfil
    with col_back:
        if st.button("⬅️ Voltar", key="assinatura_voltar_perfil", use_container_width=True):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
            st.rerun()

    # Botão de logout
    with col_logout:
        if st.button("🚪 Sair", key="logout_top", use_container_width=True):
            st.session_state.clear()
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.rerun()

    # Adicionar botão de voltar no rodapé também
    st.divider()
    if st.button("⬅️ Voltar para Perfil", key="assinatura_voltar_perfil_bottom", use_container_width=True):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()

    try:
        db = firestore.client()
        user_uid_auth = user_info.get('uid')
        if user_uid_auth:
            usuarios_query = db.collection('usuarios').where('uid', '==', user_uid_auth).limit(1).stream()
            
            usuario_doc_data = None
            for doc in usuarios_query:
                usuario_doc_data = doc.to_dict()
                break

            if usuario_doc_data:
                is_premium = usuario_doc_data.get('premium', False)
                status_conta_texto = "Premium ✨" if is_premium else "Gratuito"
                st.write(f"**Status da Conta:** {status_conta_texto}")

                # Seção de Plano Atual
                st.markdown("### 📊 Plano Atual")
                if usuario_doc_data and 'data_cadastro' in usuario_doc_data:
                    data_cadastro_ts = usuario_doc_data['data_cadastro']
                    if isinstance(data_cadastro_ts, GCloudTimestamp):
                        current_time = datetime.now(timezone.utc)
                        dias_restantes = 7 - (current_time - data_cadastro_ts).days
                        
                        if dias_restantes > 0:
                            st.info(f"Você está no plano gratuito com {dias_restantes} dias restantes de teste.")
                        else:
                            st.warning("Seu período de teste expirou. Faça upgrade para continuar usando todas as funcionalidades.")
                    else:
                        st.info("Você está no plano gratuito.")
                else:
                    st.info("Você está no plano gratuito.")

                # Seção de Upgrade de Plano (só exibe se o usuário não for premium)
                if not is_premium:
                    st.markdown("### 🚀 Faça um Upgrade no seu Plano!")
                    st.markdown("Desbloqueie todo o potencial da nossa plataforma.")

                    with st.container(border=True):
                        st.markdown("### ⭐ Seja Premium")
                        st.markdown(
                            """
                            Tenha acesso ilimitado e vantagens exclusivas:
                            - Criação **ilimitada** de projetos.
                            - Acesso a **modelos de editais avançados**.
                            - Ferramentas de **análise de viabilidade** detalhadas.
                            - **Diagnóstico IA** mais completo para seus projetos.
                            - **Geração de documentos** em múltiplos formatos.
                            - **Suporte prioritário** e personalizado.
                            - **Valor:** R$ 49,90 / mês
                            """
                        )
                        if st.button("💎 Fazer Upgrade para Premium", key="upgrade_premium_button", type="primary", use_container_width=True):
                            st.info("Redirecionando para a página de upgrade...")
                            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'pagamento_upgrade'
                            st.rerun()

                # Mostrar informações de assinatura para usuários premium
                if is_premium:
                    st.markdown("### 📅 Informações da Assinatura")
                    data_ativacao = usuario_doc_data.get('data_ativacao_premium')
                    if data_ativacao:
                        if isinstance(data_ativacao, GCloudTimestamp):
                            data_renovacao = GCloudTimestamp.from_datetime(
                                data_ativacao + timedelta(days=30)
                            )
                            st.write(f"**Data de Ativação:** {data_ativacao.strftime('%d/%m/%Y')}")
                            st.write(f"**Próxima Renovação:** {data_renovacao.strftime('%d/%m/%Y')}")
                    
                    # Botão para cancelar assinatura
                    if st.button("❌ Cancelar Assinatura", type="secondary"):
                        if st.warning("Tem certeza que deseja cancelar sua assinatura?"):
                            try:
                                # Atualizar status no Firestore
                                user_ref = db.collection('usuarios').document(user_uid_auth)
                                user_ref.update({
                                    'premium': False,
                                    'data_cancelamento': firestore.SERVER_TIMESTAMP,
                                    'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                                })
                                st.success("Sua assinatura foi cancelada com sucesso!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao cancelar assinatura: {str(e)}")

    except Exception as e:
        st.error(f"Erro ao buscar informações da assinatura: {str(e)}") 