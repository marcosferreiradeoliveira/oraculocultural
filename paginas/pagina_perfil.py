import streamlit as st
from firebase_admin import firestore
from google.cloud.firestore_v1 import FieldFilter
from google.api_core.datetime_helpers import DatetimeWithNanoseconds as GCloudTimestamp
from constants import (
    USER_SESSION_KEY, 
    AUTENTICADO_SESSION_KEY, 
    PAGINA_ATUAL_SESSION_KEY,
    PROJETO_SELECIONADO_KEY,
    TEXTO_PROJETO_KEY,
    RESUMO_KEY,
    ORCAMENTO_KEY,
    CRONOGRAMA_KEY,
    OBJETIVOS_KEY,
    JUSTIFICATIVA_KEY,
    EDITAL_SELECIONADO_KEY
)
from datetime import datetime, timedelta, timezone


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

    # Use columns to align title and buttons
    col_title, col_back, col_logout = st.columns([4, 1, 1]) # Adjust column ratios as needed

    with col_title:
        st.markdown("## Meu Perfil") # Use markdown for title consistent with section headers

    # Botão Voltar para Projetos no topo (condicional)
    if not forced_view:
        with col_back:
            if st.button("⬅️ Voltar", key="perfil_voltar_projetos_top", use_container_width=True):
                st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                st.rerun()

    # Botão de logout no topo
    with col_logout:
        if st.button("🚪 Sair", key="logout_top", use_container_width=True):
            keys_to_clear = [
                USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PROJETO_SELECIONADO_KEY,
                TEXTO_PROJETO_KEY, RESUMO_KEY, ORCAMENTO_KEY, CRONOGRAMA_KEY,
                OBJETIVOS_KEY, JUSTIFICATIVA_KEY, EDITAL_SELECIONADO_KEY
            ]
            for key in keys_to_clear:
                if key in st.session_state:
                    del st.session_state[key]
            project_specific_keys_patterns = [user_info.get('uid','temp_id_clear'), 'diagnostico_editavel', 'doc_gerado', 'projeto_para_excluir']
            keys_to_remove_session = [k for k in st.session_state if any(pattern in k for pattern in project_specific_keys_patterns)]
            for key in keys_to_remove_session:
                if key in st.session_state:
                    del st.session_state[key]
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
            st.success("Você saiu da sua conta.")
            st.rerun()

    nome_para_exibir = user_info.get("nome_completo", user_info.get("display_name", "Nome não disponível"))
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
                if usuario_doc_data.get('nome_completo'): # Prioriza nome_completo do Firestore
                    nome_para_exibir = usuario_doc_data['nome_completo']
                
                is_premium = usuario_doc_data.get('premium', False)
                is_premium_user = is_premium # Atualiza a flag
                status_conta_texto = "Premium ✨" if is_premium else "Gratuito"
                
                # Obter nome da empresa
                nome_empresa = usuario_doc_data.get('empresa', '')
                
                st.subheader(nome_para_exibir)
                st.write(f"**Nome:** {nome_para_exibir}")
                if nome_empresa:
                    st.write(f"**Empresa:** {nome_empresa}")
                st.write(f"**Email:** {email_para_exibir}")
                st.write(f"**Status da Conta:** {status_conta_texto}")

                # Botão para acessar a página de assinatura (menor)
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("💎 Gerenciar Assinatura", key="gerenciar_assinatura"):
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'assinatura'
                        st.rerun()

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
                    nome_completo = st.text_input("Nome Completo", value=usuario_doc_data.get('nome_completo', nome_para_exibir))
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
                    nome_empresa = st.text_input("Nome da Empresa", value=usuario_doc_data.get('empresa', ''))
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
                            'empresa': nome_empresa,
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

    except Exception as e:
        st.subheader(nome_para_exibir) # Exibe nome e email mesmo em caso de erro na busca do status
        st.write(f"**Email:** {email_para_exibir}")
        st.error(f"Erro ao buscar status da conta: {e}")
        st.write("**Status da Conta:** Erro ao verificar.")

    st.divider()

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
