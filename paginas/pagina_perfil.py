import streamlit as st
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY


def pagina_perfil():
    """
    Exibe a página de perfil do usuário com nome, email e status da conta.
    Inclui seção de upgrade e lógica condicional para o botão "Voltar".
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

    st.title("Meu Perfil")

    nome_para_exibir = user_info.get("nome", user_info.get("display_name", "Nome não disponível"))
    email_para_exibir = user_info.get('email', 'Email não disponível')
    is_premium_user = False # Flag para controlar a exibição da seção de upgrade
    
    # Definir forced_view aqui, antes de seu primeiro uso
    forced_view = st.session_state.get('forced_profile_view', False)

    # Buscar dados do Firestore (status e potencialmente o nome correto)
    try:
        db = firestore.client()
        user_uid_auth = user_info.get('uid') # UID do Firebase Auth
        if user_uid_auth:
            usuarios_query = db.collection('usuarios').where(filter=FieldFilter('uid', '==', user_uid_auth)).limit(1).stream()
            
            usuario_doc_data = None
            for doc in usuarios_query: # Deve haver no máximo um resultado devido ao limit(1)
                usuario_doc_data = doc.to_dict()
                break # Pegamos o primeiro (e único esperado)

            if usuario_doc_data:
                if usuario_doc_data.get('nome'): # Prioriza nome do Firestore
                    nome_para_exibir = usuario_doc_data['nome']
                
                is_premium = usuario_doc_data.get('premium', False)
                is_premium_user = is_premium # Atualiza a flag
                status_conta_texto = "Premium ✨" if is_premium else "Gratuito"
                
                st.subheader(nome_para_exibir)
                st.write(f"**Email:** {email_para_exibir}")
                st.write(f"**Status da Conta:** {status_conta_texto}")
                # A mensagem "Considere se tornar Premium" é mais relevante na seção de upgrade
            else:
                # Usuário não encontrado na coleção 'usuarios'
                st.subheader(nome_para_exibir)
                st.write(f"**Email:** {email_para_exibir}")
                st.write("**Status da Conta:** Informação não disponível (usuário não encontrado na base de dados específica).")
        else:
            # UID do usuário não encontrado em user_info
            st.subheader(nome_para_exibir)
            st.write(f"**Email:** {email_para_exibir}")
            st.write("**Status da Conta:** Não verificado (UID do usuário ausente na sessão).")

    except Exception as e:
        st.subheader(nome_para_exibir) # Exibe nome e email mesmo em caso de erro na busca do status
        st.write(f"**Email:** {email_para_exibir}")
        st.error(f"Erro ao buscar status da conta: {e}")
        st.write("**Status da Conta:** Erro ao verificar.")

    st.divider()

    # Exibir mensagem de trial expirado ANTES da seção de upgrade, se aplicável
    if forced_view and not is_premium_user:
        st.info("Seu período de teste de 24 horas expirou. Para continuar acessando seus projetos e outras funcionalidades, por favor, escolha um plano.")

    # Seção de Upgrade de Plano (só exibe se o usuário não for premium)
    if not is_premium_user:
        
        st.subheader("🚀 Faça um Upgrade no seu Plano!")
        st.markdown("Desbloqueie todo o potencial da nossa plataforma.")

        col_trial, col_premium_upgrade = st.columns(2)

        with col_trial:
            with st.container(border=True):
                st.markdown("### ⏳ Teste Premium por 1 Dia")
                st.markdown(
                    """
                    Experimente todos os recursos exclusivos do plano Premium gratuitamente por 24 horas!
                    Ideal para você conhecer na prática como podemos te ajudar a alcançar seus objetivos.
                    """
                )
                if not forced_view and st.button("✨ Iniciar Teste Gratuito (1 Dia)", key="start_trial_button", use_container_width=True):
                    st.success("Funcionalidade de teste de 1 dia ainda em desenvolvimento!")
                    # Lógica para ativar o trial no backend (ex: atualizar Firestore)

        with col_premium_upgrade:
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
                    - **Valor:** R$ 249,00 / mês
                    """
                )
                if st.button("💎 Fazer Upgrade para Premium", key="upgrade_premium_button", type="primary", use_container_width=True):
                    st.info("Redirecionando para a página de upgrade...")
                    # Lógica para redirecionar para pagamento/upgrade
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'pagamento_upgrade'
                    st.rerun()
        st.divider() # Divider após a seção de upgrade
    else:
        st.success("🎉 Você já é um usuário Premium! Aproveite todos os benefícios.")
        st.divider() # Divider se já for premium

    # Lógica para o botão "Voltar para Projetos"
    # forced_view já foi definido no início da função
    if not forced_view:
        if st.button("⬅️ Voltar para Projetos", key="perfil_voltar_projetos"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()
    # A mensagem de trial expirado já foi movida para cima, então não precisamos de um 'else' aqui
    # a menos que queiramos repetir a mensagem, o que pode ser redundante.
    
def pagina_pagamento_upgrade():
    st.title("Página de Upgrade")
    st.write("Página de upgrade em construção.  Haverá integração com métodos de pagamento aqui.")
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()
