import tempfile
from langchain_openai import ChatOpenAI

import os # Mantido para uso potencial, ex: variáveis de ambiente
import streamlit as st
from dotenv import load_dotenv # Para carregar variáveis de .env
import firebase_admin
from firebase_admin import credentials, firestore # auth será usado em login.py

# Importações de modelos e utilitários
from models import (
    get_llm,
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa
)
from loaders import carrega_pdf
# Removido: from services.firestore_service import initialize_firebase (a função está definida abaixo)

# Importações de páginas
from paginas.login import pagina_login # Página de login refatorada
from paginas.pagina_editar_projeto import pagina_editar_projeto as pagina_editar_projeto_view


st.set_page_config(
    page_title="Oráculo Cultural",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="collapsed", # Mantém a sidebar recolhida por padrão
    menu_items={
        'Get Help': None, # 'https://www.meusite.com/help',
        'Report a bug': None, # "mailto:contato@meusite.com",
        'About': "# Oráculo Cultural\nSua plataforma para decifrar o universo da cultura."
    }
)
# Constantes para nomes de chave do session_state
USER_SESSION_KEY = 'user'
AUTENTICADO_SESSION_KEY = 'autenticado'
PAGINA_ATUAL_SESSION_KEY = 'pagina_atual'
PROJETO_SELECIONADO_KEY = 'projeto_selecionado'
TEXTO_PROJETO_KEY = 'texto_projeto' # Para o texto do PDF carregado
# Para documentos gerados
RESUMO_KEY = 'resumo'
ORCAMENTO_KEY = 'orcamento'
CRONOGRAMA_KEY = 'cronograma'
OBJETIVOS_KEY = 'objetivos'
JUSTIFICATIVA_KEY = 'justificativa'
openai_api_key = st.secrets["openai"]["api_key"]
llm = ChatOpenAI(
    openai_api_key=openai_api_key,
    model="gpt-3.5-turbo"
)


# Inicialização do Firebase (deve ser chamada uma vez)
def initialize_firebase():
    if not firebase_admin._apps:
        try:
            # Carrega as credenciais do Secrets
            firebase_config = st.secrets["firebase_credentials"]
            
            # Prepara o dicionário de credenciais
            cred_dict = {
                "type": firebase_config["type"],
                "project_id": firebase_config["project_id"],
                "private_key_id": firebase_config["private_key_id"],
                "private_key": firebase_config["private_key"].replace('\\n', '\n'),
                "client_email": firebase_config["client_email"],
                "client_id": firebase_config["client_id"],
                "auth_uri": firebase_config["auth_uri"],
                "token_uri": firebase_config["token_uri"],
                "auth_provider_x509_cert_url": firebase_config["auth_provider_x509_cert_url"],
                "client_x509_cert_url": firebase_config["client_x509_cert_url"],
                "universe_domain": firebase_config.get("universe_domain", "googleapis.com")
            }
            
            # Inicializa o Firebase
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            st.success("Conexão com Firebase estabelecida!")
        except Exception as e:
            st.error(f"Erro ao conectar ao Firebase: {str(e)}")
            st.stop()

# Chama a função de inicialização
initialize_firebase()
# Carrega variáveis de ambiente do arquivo .env (se existir)
load_dotenv()

# Configuração inicial da página Streamlit
# Deve ser a primeira chamada Streamlit, exceto para comentários e imports


# CSS customizado global (aplicado a todas as páginas, exceto se sobrescrito)
# O CSS da página de login agora está em paginas/login.py
st.markdown("""
    <style>
        /* Esconde o menu lateral padrão e ícone de hamburger globalmente */
        /* A menos que a página de login precise deles visíveis, o que não é o caso */
        /* div[data-testid="stSidebarNav"], div[data-testid="collapsedControl"] {
            display: none !important;
        } */
        
        /* Esconde o menu padrão do Streamlit (MainMenu) e o rodapé (footer) */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Remove padding extra no topo do app se não for a página de login */
        /* Ajuste fino pode ser necessário dependendo da estrutura das outras páginas */
        /* .stApp > div:first-child > div:first-child > div:first-child { padding-top: 1rem; } */

        /* Estilo para cartões de projetos (usado em pagina_projetos) */
        .project-card {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 1.5rem; /* Aumentado o padding */
            margin-bottom: 1rem;
            box-shadow: 0 4px 8px rgba(0,0,0,0.1); /* Sombra um pouco mais pronunciada */
            transition: transform 0.2s ease-in-out, box-shadow 0.2s ease-in-out;
        }
        .project-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }
        .project-card h3 {
            margin-top: 0;
            margin-bottom: 0.75rem;
            color: #333;
        }
        .project-card p {
            margin-bottom: 0.5rem;
            font-size: 0.9rem;
            color: #555;
        }

        /* Ajustes de responsividade para o container principal em telas maiores */
        @media screen and (min-width: 1024px) {
            .main .block-container {
                max-width: 90%; /* Ou o valor que preferir, ex: 1200px */
                /* padding-left: 2rem; */ /* Removido para usar o padding padrão ou específico da página */
                /* padding-right: 2rem; */
            }
        }
    </style>
""", unsafe_allow_html=True)


# Função para recuperar projetos do usuário do Firestore
def get_user_projects(user_id):
    """Recupera os projetos de um usuário específico do Firestore."""
    try:
        db = firestore.client()
        projetos_ref = db.collection('projetos').where('user_id', '==', user_id).order_by('data_criacao', direction=firestore.Query.DESCENDING)
        projetos_stream = projetos_ref.stream() # Renomeado para evitar conflito com a lista
        projetos_lista = [{'id': doc.id, **doc.to_dict()} for doc in projetos_stream]
        return projetos_lista
    except Exception as e:
        st.error(f"Erro ao recuperar projetos: {str(e)}")
        return []

# Página de Projetos
def pagina_projetos():
    """Exibe a página de listagem de projetos do usuário."""
    if not st.session_state.get(USER_SESSION_KEY):
        st.warning("Usuário não logado.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()
        return

    st.title(f'Bem-vindo(a), {st.session_state[USER_SESSION_KEY]["email"]}!')
    
    if st.button("Sair", key="logout_button_projetos"):
        # Limpa o estado da sessão relacionado ao usuário
        for key in [USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PROJETO_SELECIONADO_KEY, TEXTO_PROJETO_KEY, RESUMO_KEY, ORCAMENTO_KEY, CRONOGRAMA_KEY, OBJETIVOS_KEY, JUSTIFICATIVA_KEY]:
            if key in st.session_state:
                del st.session_state[key]
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login' # Define a página de login como a próxima
        st.success("Você saiu da sua conta.")
        st.rerun()
    
    projetos = get_user_projects(st.session_state[USER_SESSION_KEY]['uid'])
    
    st.header('Meus Projetos Culturais', divider='rainbow')
    
    # Botão para criar novo projeto sempre visível no topo
    if st.button("🎨 Criar Novo Projeto", type="primary", use_container_width=False): # Ajuste use_container_width conforme preferir
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'novo_projeto'
        # Limpa dados de projeto selecionado ou texto de projeto anterior
        if PROJETO_SELECIONADO_KEY in st.session_state: del st.session_state[PROJETO_SELECIONADO_KEY]
        if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
        st.rerun()

    if not projetos:
        st.markdown("""
            <div style="text-align: center; padding: 3rem 1rem; background-color: #e9ecef; border-radius: 10px; margin-top: 2rem;">
                <h3>Você ainda não tem projetos cadastrados.</h3>
                <p>Clique em "Criar Novo Projeto" para começar sua jornada cultural!</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        # Exibição dos projetos em colunas responsivas
        # Define o número de colunas com base na largura da tela (aproximação)
        # Este é um placeholder, Streamlit não tem detecção de largura de tela direta para Python.
        # Para um layout verdadeiramente responsivo de colunas, considere o número de itens.
        num_cols = 3 # min(len(projetos), 3) # Exibe no máximo 3 colunas
        
        cols = st.columns(num_cols)
        for i, projeto in enumerate(projetos):
            col_index = i % num_cols
            with cols[col_index]:
                # Usando st.markdown para aplicar a classe .project-card
                st.markdown(f""" 
                <div class="project-card">
                    <h3>{projeto.get('nome', 'Projeto sem nome')}</h3>
                    <p><strong>Categoria:</strong> {projeto.get('categoria', 'Não definida')}</p>
                    <p>{projeto.get('descricao', 'Sem descrição')[:100]}...</p>
                </div>
                """, unsafe_allow_html=True)
                # Botões dentro de um container normal do Streamlit para funcionalidade
                # Idealmente, os botões seriam parte do card HTML, mas isso complica a interatividade do Streamlit
                
                # Botões de ação para cada projeto
                btn_cols = st.columns(2)
                with btn_cols[0]:
                    if st.button(f"📝 Editar", key=f"editar_{projeto['id']}", use_container_width=True):
                        st.session_state[PROJETO_SELECIONADO_KEY] = projeto
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'editar_projeto'
                        st.rerun()
                with btn_cols[1]:
                    if st.button(f"🔍 Detalhes", key=f"detalhes_{projeto['id']}", use_container_width=True):
                        st.session_state[PROJETO_SELECIONADO_KEY] = projeto
                        # Limpa documentos gerados anteriormente ao ver detalhes de um novo projeto
                        for key_doc in [RESUMO_KEY, ORCAMENTO_KEY, CRONOGRAMA_KEY, OBJETIVOS_KEY, JUSTIFICATIVA_KEY, TEXTO_PROJETO_KEY]:
                            if key_doc in st.session_state: del st.session_state[key_doc]
                        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'detalhes_projeto'
                        st.rerun()
                st.markdown("---") # Separador visual entre os cards na mesma coluna


# Página para Criar Novo Projeto
def pagina_novo_projeto():
    """Exibe o formulário para criar um novo projeto cultural."""
    st.header('✨ Criar Novo Projeto Cultural')
    
    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto*", help="O título principal do seu projeto.")
        descricao = st.text_area("Descrição Detalhada do Projeto*", height=150, help="Descreva os objetivos, público-alvo, e o que torna seu projeto único.")
        categoria = st.selectbox("Categoria Principal*", [
            "Artes Visuais", "Música", "Teatro", "Dança", 
            "Cinema e Audiovisual", "Literatura e Publicações", 
            "Patrimônio Cultural", "Artesanato", "Cultura Popular", "Outra"
        ], help="Selecione a categoria que melhor descreve seu projeto.")
        
        # Adicionar mais campos se necessário (ex: data de início, local, etc.)

        submitted = st.form_submit_button("🚀 Salvar Projeto")
        
        if submitted:
            if not nome or not descricao or not categoria:
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
            else:
                try:
                    db = firestore.client()
                    user_uid = st.session_state.get(USER_SESSION_KEY, {}).get('uid')
                    if not user_uid:
                        st.error("Erro: Usuário não identificado. Faça login novamente.")
                        return

                    novo_projeto_data = {
                        'nome': nome,
                        'descricao': descricao,
                        'categoria': categoria,
                        'user_id': user_uid,
                        'data_criacao': firestore.SERVER_TIMESTAMP,
                        'data_atualizacao': firestore.SERVER_TIMESTAMP,
                        # Adicione outros campos conforme necessário
                    }
                    
                    # Salva o novo projeto no Firestore
                    db.collection('projetos').add(novo_projeto_data)
                    
                    st.success(f"Projeto '{nome}' criado com sucesso!")
                    st.balloons()
                    
                    # Redireciona para a página de projetos
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {str(e)}")
    
    if st.button("⬅️ Voltar para Projetos"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun()


# Função para mostrar detalhes do projeto e gerar documentos
def pagina_detalhes_projeto():
    """Exibe os detalhes de um projeto selecionado e opções para gerar documentos."""
    projeto = st.session_state.get(PROJETO_SELECIONADO_KEY)
    
    if not projeto:
        st.warning("Nenhum projeto selecionado. Retornando à lista de projetos.")
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        st.rerun()
        return

    st.header(f'🔍 Detalhes do Projeto: {projeto.get("nome", "Sem Nome")}')
    st.caption(f"Categoria: {projeto.get('categoria', 'N/A')}")
    st.markdown(f"**Descrição:**\n {projeto.get('descricao', 'Sem descrição.')}")
    st.markdown("---")

    # Opções de geração de documentos
    st.subheader("📑 Assistente de Geração de Documentos", divider='blue')
    
    # Carregamento do PDF do projeto
    if TEXTO_PROJETO_KEY not in st.session_state:
        st.info("⚠️ Para gerar os documentos, por favor, carregue o arquivo PDF principal do seu projeto.")
        arquivo_pdf = st.file_uploader("Selecione o arquivo PDF do projeto", type=["pdf"], key="pdf_uploader_detalhes")

        if arquivo_pdf:
            with st.spinner("Processando PDF... Por favor, aguarde."):
                try:
                    # Salva o arquivo temporariamente para leitura
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(arquivo_pdf.getvalue())
                        caminho_tmp_pdf = tmp_file.name
                    
                    texto_extraido = carrega_pdf(caminho_tmp_pdf) # Função que extrai texto do PDF
                    os.remove(caminho_tmp_pdf) # Remove o arquivo temporário

                    if texto_extraido:
                        st.session_state[TEXTO_PROJETO_KEY] = texto_extraido
                        st.success("✅ PDF carregado e processado com sucesso!")
                        st.rerun() # Recarrega para mostrar as abas de geração
                    else:
                        st.error("Não foi possível extrair texto do PDF. Tente outro arquivo ou verifique o formato.")
                except Exception as e:
                    st.error(f"Erro ao processar PDF: {e}")
                    if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY] # Limpa em caso de erro
    
    if TEXTO_PROJETO_KEY in st.session_state:
        texto_base_projeto = st.session_state[TEXTO_PROJETO_KEY]
        st.success("Pronto para gerar documentos com base no PDF carregado!")

        # Abas para cada tipo de documento a ser gerado
        tab_titles = ["📝 Resumo", "💰 Orçamento", "📅 Cronograma", "🎯 Objetivos", "📚 Justificativa"]
        tabs = st.tabs(tab_titles)

        doc_generators = {
            "Resumo": (gerar_resumo_projeto, RESUMO_KEY),
            "Orçamento": (gerar_orcamento, ORCAMENTO_KEY),
            "Cronograma": (gerar_cronograma, CRONOGRAMA_KEY),
            "Objetivos": (gerar_objetivos, OBJETIVOS_KEY),
            "Justificativa": (gerar_justificativa, JUSTIFICATIVA_KEY),
        }

        for i, title_prefix in enumerate(tab_titles):
            doc_type = title_prefix.split(" ")[1] # Ex: "Resumo"
            generator_func, session_key = doc_generators[doc_type]
            
            with tabs[i]:
                st.markdown(f"#### Gerar {doc_type} do Projeto")
                if st.button(f"Gerar {doc_type} Agora", key=f"gerar_{doc_type.lower()}_btn"):
                    with st.spinner(f"Elaborando {doc_type}... Isso pode levar alguns instantes."):
                        try:
                            llm_instance = get_llm() # Obtém a instância do LLM
                            documento_gerado = generator_func(llm_instance, texto_base_projeto)
                            st.session_state[session_key] = documento_gerado
                            st.success(f"✅ {doc_type} gerado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao gerar {doc_type}: {e}")
                
                if session_key in st.session_state:
                    st.subheader(f"Visualização do {doc_type}:")
                    st.markdown(f"```\n{st.session_state[session_key]}\n```" if doc_type in ["Orçamento", "Cronograma"] else st.session_state[session_key]) # Usa ``` para preservar formatação
                    st.download_button(
                        label=f"📥 Baixar {doc_type}",
                        data=st.session_state[session_key].encode('utf-8'), # Garante encoding para download
                        file_name=f"{doc_type.lower()}_{projeto.get('nome', 'projeto').replace(' ', '_')}.txt",
                        mime="text/plain",
                        key=f"download_{doc_type.lower()}"
                    )
        st.markdown("---")
        if st.button("🗑️ Recarregar outro PDF", key="recarregar_pdf_btn"):
            if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
            # Limpa também os documentos gerados para evitar confusão
            for _, session_k in doc_generators.values():
                if session_k in st.session_state: del st.session_state[session_k]
            st.rerun()


    # Botão para voltar
    if st.button("⬅️ Voltar para Lista de Projetos", key="voltar_detalhes_projetos"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
        # Limpa o projeto selecionado e o texto do PDF ao voltar para a lista
        if PROJETO_SELECIONADO_KEY in st.session_state: del st.session_state[PROJETO_SELECIONADO_KEY]
        if TEXTO_PROJETO_KEY in st.session_state: del st.session_state[TEXTO_PROJETO_KEY]
        for _, session_k_doc in doc_generators.values(): # Limpa documentos gerados
            if session_k_doc in st.session_state: del session_k_doc
        st.rerun()


# Fluxo Principal da Aplicação (Router)
def main():
    """Função principal que controla o fluxo de páginas da aplicação."""
    if not initialize_firebase_app(): # Tenta inicializar o Firebase para o app
        st.error("Falha crítica na inicialização do Firebase. A aplicação não pode continuar.")
        st.stop() # Impede a execução se o Firebase não puder ser inicializado

    # Inicializa o estado da sessão se as chaves não existirem
    if AUTENTICADO_SESSION_KEY not in st.session_state:
        st.session_state[AUTENTICADO_SESSION_KEY] = False
    if USER_SESSION_KEY not in st.session_state:
        st.session_state[USER_SESSION_KEY] = None
    if PAGINA_ATUAL_SESSION_KEY not in st.session_state:
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login' # Começa na página de login

    # Roteamento de páginas
    if not st.session_state[AUTENTICADO_SESSION_KEY]:
        pagina_login() # Se não autenticado, mostra a página de login
    else:
        # Usuário autenticado, navega para a página atual definida no estado da sessão
        current_page = st.session_state[PAGINA_ATUAL_SESSION_KEY]
        if current_page == 'projetos':
            pagina_projetos()
        elif current_page == 'novo_projeto':
            pagina_novo_projeto()
        elif current_page == 'editar_projeto':
            # pagina_editar_projeto() # Chama a função importada
            pagina_editar_projeto_view() # Usando o alias da importação
        elif current_page == 'detalhes_projeto':
            pagina_detalhes_projeto()
        else:
            # Fallback: se a página atual for desconhecida, volta para a página de projetos
            st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'
            st.rerun()

if __name__ == '__main__':
    main()
