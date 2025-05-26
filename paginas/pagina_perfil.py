import streamlit as st
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY
from datetime import datetime, timedelta


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

    # Definir forced_view no início da função
    forced_view = st.session_state.get('forced_profile_view', False)

    st.title("Meu Perfil")

    # Botão Voltar para Projetos no topo
    if not forced_view:
        if st.button("⬅️ Voltar para Projetos", key="perfil_voltar_projetos_top"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()

    nome_para_exibir = user_info.get("nome", user_info.get("display_name", "Nome não disponível"))
    email_para_exibir = user_info.get('email', 'Email não disponível')
    is_premium_user = False
    data_ativacao = None
    data_renovacao = None
    
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
                
                # Obter data de ativação e calcular data de renovação
                if is_premium and usuario_doc_data.get('data_ativacao_premium'):
                    data_ativacao = usuario_doc_data['data_ativacao_premium']
                    # Calcular data de renovação (30 dias após ativação)
                    if isinstance(data_ativacao, Timestamp):
                        data_renovacao = Timestamp.from_datetime(
                            data_ativacao.to_datetime() + timedelta(days=30)
                        )
                
                st.subheader(nome_para_exibir)
                st.write(f"**Email:** {email_para_exibir}")
                st.write(f"**Status da Conta:** {status_conta_texto}")

                # Exibir mensagem de trial expirado ANTES da seção de biografia, se aplicável
                if forced_view and not is_premium_user:
                    st.info("Seu período de teste de 24 horas expirou. Para continuar acessando seus projetos e outras funcionalidades, por favor, escolha um plano.")

                # Seção de Biografia Profissional
                st.divider()
                st.subheader("📝 Biografia Profissional")
                bio_profissional = usuario_doc_data.get('bio_profissional', '')
                nova_bio = st.text_area("Sua biografia profissional", value=bio_profissional, height=150)
                
                # Botão de salvar fora do text_area para evitar re-renders
                if st.button("💾 Salvar Biografia", key="salvar_bio"):
                    try:
                        # Encontrar o documento do usuário pelo UID
                        usuarios_query = db.collection('usuarios').where(filter=FieldFilter('uid', '==', user_uid_auth)).limit(1).stream()
                        for doc in usuarios_query:
                            doc_ref = db.collection('usuarios').document(doc.id)
                            doc_ref.update({
                                'bio_profissional': nova_bio,
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            st.success("✅ Biografia atualizada com sucesso!")
                            st.rerun()
                            break
                    except Exception as e:
                        st.error(f"Erro ao atualizar biografia: {str(e)}")

                # Seção de Dados Cadastrais
                st.divider()
                st.subheader("👤 Dados Cadastrais")
                
                # Criar colunas para melhor organização
                col1, col2 = st.columns(2)
                
                with col1:
                    nome_completo = st.text_input("Nome Completo", value=usuario_doc_data.get('nome_completo', ''))
                    rg = st.text_input("RG", value=usuario_doc_data.get('rg', ''))
                    orgao_emissor = st.text_input("Órgão Emissor", value=usuario_doc_data.get('orgao_emissor', ''))
                    
                    # Formatar data de emissão
                    data_emissao_firestore = usuario_doc_data.get('data_emissao')
                    if data_emissao_firestore:
                        try:
                            data_emissao_default = datetime.fromisoformat(data_emissao_firestore)
                        except:
                            data_emissao_default = datetime.now()
                    else:
                        data_emissao_default = datetime.now()
                    data_emissao = st.date_input(
                        "Data de Emissão",
                        value=data_emissao_default,
                        format="DD-MM-YYYY"
                    )
                    
                    cpf = st.text_input("CPF", value=usuario_doc_data.get('cpf', ''))
                    
                    # Formatar data de nascimento
                    data_nascimento_firestore = usuario_doc_data.get('data_nascimento')
                    if data_nascimento_firestore:
                        try:
                            data_nascimento_default = datetime.fromisoformat(data_nascimento_firestore)
                        except:
                            data_nascimento_default = datetime.now()
                    else:
                        data_nascimento_default = datetime.now()
                    data_nascimento = st.date_input(
                        "Data de Nascimento",
                        value=data_nascimento_default,
                        format="DD-MM-YYYY"
                    )
                
                with col2:
                    endereco = st.text_area("Endereço", value=usuario_doc_data.get('endereco', ''))
                    nome_empresa = st.text_input("Nome da Empresa", value=usuario_doc_data.get('nome_empresa', ''))
                    endereco_empresa = st.text_area("Endereço da Empresa", value=usuario_doc_data.get('endereco_empresa', ''))
                    cnpj = st.text_input("CNPJ da Empresa", value=usuario_doc_data.get('cnpj', ''))
                    bio_empresa = st.text_area("Biografia da Empresa", value=usuario_doc_data.get('bio_empresa', ''), height=100)

                if st.button("Salvar Dados Cadastrais"):
                    try:
                        dados_atualizados = {
                            'nome_completo': nome_completo,
                            'rg': rg,
                            'orgao_emissor': orgao_emissor,
                            'data_emissao': data_emissao.isoformat(),
                            'cpf': cpf,
                            'data_nascimento': data_nascimento.isoformat(),
                            'endereco': endereco,
                            'nome_empresa': nome_empresa,
                            'endereco_empresa': endereco_empresa,
                            'cnpj': cnpj,
                            'bio_empresa': bio_empresa,
                            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                        }
                        
                        user_ref = db.collection('usuarios').document(user_uid_auth)
                        user_ref.update(dados_atualizados)
                        st.success("Dados cadastrais atualizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar dados cadastrais: {str(e)}")

                # Mostrar informações de assinatura para usuários premium
                if is_premium_user:
                    st.divider()
                    st.subheader("📅 Informações da Assinatura")
                    if data_ativacao:
                        st.write(f"**Data de Ativação:** {data_ativacao.strftime('%d/%m/%Y')}")
                    if data_renovacao:
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
                    - **Valor:** R$ 99,00 / mês
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

    # Lógica para o botão "Voltar para Projetos" no rodapé
    if not forced_view:
        st.divider()  # Adiciona uma linha divisória antes do botão
        if st.button("⬅️ Voltar para Projetos", key="perfil_voltar_projetos_bottom"):
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()
    
def pagina_pagamento_upgrade():
    st.title("Página de Upgrade")
    st.write("Página de upgrade em construção.  Haverá integração com métodos de pagamento aqui.")
    if st.button("Voltar para Perfil"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'perfil'
        st.rerun()
