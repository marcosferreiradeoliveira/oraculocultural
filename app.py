import tempfile
import os
import streamlit as st
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth, firestore
from models import (
    get_llm,
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa)
from loaders import carrega_pdf

# Configuração inicial
st.set_page_config(
    page_title="Oráculo Cultural - Edital Vale", 
    page_icon="🎭",
    layout="wide",  # Changed to wide for better desktop responsiveness
    initial_sidebar_state="collapsed"
)

# CSS customizado com melhorias de responsividade
st.markdown("""
    <style>
        /* Esconde o menu padrão do Streamlit */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Botão de login */
        .stButton>button {
            background-color: #e74c3c;
            color: white;
            border: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            width: 100%;
        }
        
        /* Campos de input */
        .stTextInput>div>div>input, .stTextArea>div>div>textarea {
            padding: 0.5rem;
        }

        /* Ajustes de responsividade */
        @media screen and (min-width: 1024px) {
            .main .block-container {
                max-width: 90%;
                padding-left: 2rem;
                padding-right: 2rem;
            }
        }

        /* Estilo para cartões de projetos */
        .project-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1rem;
            margin-bottom: 1rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
    </style>
""", unsafe_allow_html=True)

# Carrega variáveis de ambiente
load_dotenv()

# Inicialização do Firebase
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            cred_path = "config/firebase-service-account.json"
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            return True
        except Exception as e:
            st.error(f"Erro ao inicializar Firebase: {str(e)}")
            return False
    return True

# Função para recuperar projetos do usuário
def get_user_projects(user_id):
    try:
        db = firestore.client()
        projetos_ref = db.collection('projetos').where('user_id', '==', user_id)
        projetos = projetos_ref.stream()
        return [{'id': doc.id, **doc.to_dict()} for doc in projetos]
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []

# Página de Login
def pagina_login():
    with st.container():
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

# Página de Projetos
def pagina_projetos():
    st.title(f'Bem-vindo, {st.session_state.user["email"]}!')
    
    if st.button("Sair", key="logout_button"):
        st.session_state.clear()
        st.rerun()
    
    # Recuperar projetos do usuário
    projetos = get_user_projects(st.session_state.user['uid'])
    
    st.header('Meus Projetos', divider=True)
    
    # Listar projetos existentes
    if not projetos:
        # Criar um container centralizado para o botão quando não há projetos
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="text-align: center; padding: 2rem; background-color: #f8f9fa; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3>Você ainda não tem projetos</h3>
                <p>Comece criando seu primeiro projeto!</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Botão de criar projeto mais proeminente
            if st.button("Criar Primeiro Projeto", use_container_width=True, type="primary"):
                st.session_state['pagina_atual'] = 'novo_projeto'
                st.rerun()
    else:
        # Botão para criar novo projeto no topo
        st.markdown('<div style="text-align: right; margin-bottom: 1rem;">', unsafe_allow_html=True)
        if st.button("+ Criar Novo Projeto"):
            st.session_state['pagina_atual'] = 'novo_projeto'
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

        # Layout de grid para projetos
        cols = st.columns(3)  # 3 colunas para desktop
        for i, projeto in enumerate(projetos):
            col = cols[i % 3]
            with col:
                with st.container(border=True):
                    st.markdown(f"""
                        <div class="project-card">
                            <h3>{projeto.get('nome', 'Projeto sem nome')}</h3>
                            <p><strong>Categoria:</strong> {projeto.get('categoria', 'Não definida')}</p>
                            <p>{projeto.get('descricao', 'Sem descrição')[:100]}...</p>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    # Botões de ação para cada projeto
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"Editar #{projeto['id']}", key=f"editar_{projeto['id']}"):
                            st.session_state['projeto_selecionado'] = projeto
                            st.session_state['pagina_atual'] = 'editar_projeto'
                            st.rerun()
                    with col2:
                        if st.button(f"Detalhes #{projeto['id']}", key=f"detalhes_{projeto['id']}"):
                            st.session_state['projeto_selecionado'] = projeto
                            st.session_state['pagina_atual'] = 'detalhes_projeto'
                            st.rerun()

# Página para Criar Novo Projeto
def pagina_novo_projeto():
    st.header('✨ Criar Novo Projeto')
    
    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto")
        descricao = st.text_area("Descrição do Projeto")
        categoria = st.selectbox("Categoria", [
            "Artes Visuais", 
            "Música", 
            "Teatro", 
            "Dança", 
            "Cinema", 
            "Literatura"
        ])
        
        if st.form_submit_button("Salvar Projeto"):
            try:
                db = firestore.client()
                novo_projeto = {
                    'nome': nome,
                    'descricao': descricao,
                    'categoria': categoria,
                    'user_id': st.session_state.user['uid'],
                    'data_criacao': firestore.SERVER_TIMESTAMP
                }
                
                # Salvar projeto no Firestore
                doc_ref = db.collection('projetos').add(novo_projeto)
                
                st.success(f"Projeto '{nome}' criado com sucesso!")
                
                # Redirecionar para página de projetos
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao salvar projeto: {str(e)}")

# Função para editar projeto
def pagina_editar_projeto():
    projeto = st.session_state.get('projeto_selecionado', {})
    
    st.header(f'✏️ Editar Projeto: {projeto.get("nome", "Sem Nome")}')
    
    with st.form("editar_projeto_form"):
        nome = st.text_input("Nome do Projeto", value=projeto.get('nome', ''))
        descricao = st.text_area("Descrição do Projeto", value=projeto.get('descricao', ''))
        categoria = st.selectbox("Categoria", [
            "Artes Visuais", 
            "Música", 
            "Teatro", 
            "Dança", 
            "Cinema", 
            "Literatura"
        ], index=[
            "Artes Visuais", 
            "Música", 
            "Teatro", 
            "Dança", 
            "Cinema", 
            "Literatura"
        ].index(projeto.get('categoria', 'Artes Visuais')))
        
        if st.form_submit_button("Atualizar Projeto"):
            try:
                db = firestore.client()
                projeto_atualizado = {
                    'nome': nome,
                    'descricao': descricao,
                    'categoria': categoria,
                    'data_atualizacao': firestore.SERVER_TIMESTAMP
                }
                
                # Atualizar projeto no Firestore
                db.collection('projetos').document(projeto['id']).update(projeto_atualizado)
                
                st.success(f"Projeto '{nome}' atualizado com sucesso!")
                
                # Redirecionar para página de projetos
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao atualizar projeto: {str(e)}")
    
    # Botão para voltar
    if st.button("Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun()

# Função para mostrar detalhes do projeto
def pagina_detalhes_projeto():
    projeto = st.session_state.get('projeto_selecionado', {})
    
    st.header(f'🔍 Detalhes do Projeto: {projeto.get("nome", "Sem Nome")}')
    
    # Opções de geração de documentos
    st.header("📑 Geração de Documentos", divider=True)
    
    # Verificar se o projeto tem um PDF carregado
    if 'texto_projeto' not in st.session_state:
        st.info("⚠️ Carregue um PDF do projeto para gerar documentos.")
        arquivo = st.file_uploader("Selecione o arquivo PDF do projeto", type=["pdf"])

        if arquivo:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as temp:
                temp.write(arquivo.read())
                texto_projeto = carrega_pdf(temp.name)
                st.session_state['texto_projeto'] = texto_projeto
                st.success("✅ Documento carregado com sucesso!")
    
    if 'texto_projeto' in st.session_state:
        # Tabs para geração de documentos
        tabs = st.tabs(["📝 Resumo", "💰 Orçamento", "📅 Cronograma", "🎯 Objetivos", "📚 Justificativa"])

        with tabs[0]:
            if st.button("Gerar Resumo"):
                with st.spinner("Criando..."):
                    st.session_state['resumo'] = gerar_resumo_projeto(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Resumo pronto.")
            if 'resumo' in st.session_state:
                st.subheader("📝 Resumo")
                st.write(st.session_state['resumo'])

        with tabs[1]:
            if st.button("Gerar Orçamento"):
                with st.spinner("Criando..."):
                    st.session_state['orcamento'] = gerar_orcamento(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Orçamento pronto.")
            if 'orcamento' in st.session_state:
                st.subheader("💰 Orçamento")
                st.write(st.session_state['orcamento'])

        with tabs[2]:
            if st.button("Gerar Cronograma"):
                with st.spinner("Criando..."):
                    st.session_state['cronograma'] = gerar_cronograma(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Cronograma pronto.")
            if 'cronograma' in st.session_state:
                st.subheader("📅 Cronograma")
                st.write(st.session_state['cronograma'])

        with tabs[3]:
            if st.button("Gerar Objetivos SMART"):
                with st.spinner("Criando..."):
                    st.session_state['objetivos'] = gerar_objetivos(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Objetivos prontos.")
            if 'objetivos' in st.session_state:
                st.subheader("🎯 Objetivos")
                st.write(st.session_state['objetivos'])

        with tabs[4]:
            if st.button("Gerar Justificativa Técnica"):
                with st.spinner("Criando..."):
                    st.session_state['justificativa'] = gerar_justificativa(get_llm(), st.session_state['texto_projeto'])
                    st.success("✅ Justificativa pronta.")
            if 'justificativa' in st.session_state:
                st.subheader("📚 Justificativa Técnica")
                st.write(st.session_state['justificativa'])

        # Área de download
        st.divider()
        with st.expander("💾 Baixar Documentos Gerados"):
            doc_cols = st.columns(4)
            if 'resumo' in st.session_state:
                doc_cols[0].download_button("⏬ Resumo", st.session_state['resumo'], "resumo.txt")
            if 'orcamento' in st.session_state:
                doc_cols[1].download_button("⏬ Orçamento", st.session_state['orcamento'], "orcamento.txt")
            if 'cronograma' in st.session_state:
                doc_cols[2].download_button("⏬ Cronograma", st.session_state['cronograma'], "cronograma.txt")
            if 'objetivos' in st.session_state:
                doc_cols[3].download_button("⏬ Objetivos", st.session_state['objetivos'], "objetivos.txt")
            if 'justificativa' in st.session_state:
                st.download_button("⏬ Justificativa", st.session_state['justificativa'], "justificativa.txt")
    
    # Botão para voltar
    if st.button("Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun()

# Fluxo Principal
def main():
    if not initialize_firebase():
        st.stop()

    # Inicializa estado da sessão
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    
    # Verificação de autenticação
    if not st.session_state.get('autenticado'):
        pagina_login()
        st.stop()
    
    # Roteamento de páginas
    pagina_atual = st.session_state.get('pagina_atual', 'projetos')
    
    if pagina_atual == 'projetos':
        pagina_projetos()
    elif pagina_atual == 'novo_projeto':
        pagina_novo_projeto()
    elif pagina_atual == 'editar_projeto':
        pagina_editar_projeto()
    elif pagina_atual == 'detalhes_projeto':
        pagina_detalhes_projeto()

if __name__ == '__main__':
    main()