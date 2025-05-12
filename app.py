import tempfile
import os
import streamlit as st
from langchain.memory import ConversationBufferMemory
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, auth
from models import (
    get_llm,
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa)
from loaders import carrega_pdf
from analise import (
    avaliar_contra_edital,
    comparar_com_selecionados
)

# Configuração inicial
st.set_page_config(
    page_title="Oráculo Cultural - Edital Vale", 
    page_icon="🎭",
    layout="centered",  # Layout centralizado
    initial_sidebar_state="collapsed"  # Esconde a sidebar
)
cred_path = "config/firebase-service-account.json"
if not os.path.exists(cred_path):
    st.error(f"Arquivo de credencial não encontrado: {cred_path}")
    st.stop()
# CSS customizado
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
        .stTextInput>div>div>input {
            padding: 0.5rem;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown("""
    <style>
        @media screen and (max-width: 600px) {
            .login-box {
                padding: 1rem !important;
            }
            .stImage {
                width: 200px !important;
            }
        }
    </style>
""", unsafe_allow_html=True)

# Carrega variáveis de ambiente
load_dotenv()

# Constantes
TIPOS_ARQUIVOS_VALIDOS = ['Site', 'Youtube', 'Pdf', 'Csv', 'Txt']
MODELO_PADRAO = "gpt-4-turbo"
MEMORIA = ConversationBufferMemory()

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

# Página de Login
def pagina_login():
    # Container principal com layout centralizado
    with st.container():
        col1, col2, col3 = st.columns([1, 3, 1])
        
        with col2:
            # Exibe a logo
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
            
            # Rodapé
            st.markdown("""
                <div style="text-align: center; margin-top: 2rem; color: #7f8c8d;">
                    <p>Em caso de problemas, contate: <a href="mailto:edital@institutoculturalvale.org">edital@institutoculturalvale.org</a></p>
                </div>
            """, unsafe_allow_html=True)
# Página Inicial após Login
def pagina_inicial():
    st.title(f'Bem-vindo, {st.session_state.user["email"]}!')
    
    if st.button("Sair"):
        st.session_state.clear()
        st.rerun()  # Atualizado para st.rerun()
    
    st.header('Escolha o tipo de projeto', divider=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button('Já tenho um projeto', use_container_width=True):
            st.session_state['fluxo'] = 'projeto_existente'
            st.rerun()  # Atualizado para st.rerun()
    with col2:
        if st.button('Quero criar um novo projeto', use_container_width=True):
            st.session_state['fluxo'] = 'novo_projeto'
            st.rerun()  # Atualizado para st.rerun()

# Páginas de Projetos
def pagina_projeto_existente():
    st.title("🧠 Oráculo Cultural – Projeto Existente")

    # === Upload do PDF (Horizontal, abaixo do título) ===
    with st.container():
        st.subheader("📤 Carregue seu Projeto em PDF")
        arquivo = st.file_uploader("Selecione o arquivo", type=["pdf"])

        if arquivo:
            with tempfile.NamedTemporaryFile(suffix=".pdf") as temp:
                temp.write(arquivo.read())
                texto_projeto = carrega_pdf(temp.name)
                st.session_state['texto_projeto'] = texto_projeto
                st.success("✅ Documento carregado com sucesso!")

    if 'texto_projeto' not in st.session_state:
        st.info("⚠️ Envie um arquivo PDF acima para continuar.")
        return

    # === Layout com menu lateral ===
    col_menu, col_conteudo = st.columns([1, 3], gap="medium")

    with col_menu:
        st.subheader("Etapas")
        etapa = st.radio(
            "Selecione uma etapa",
            ["🔍 Análise do Projeto", "📑 Gerar Documentos"],
            index=0,
            label_visibility="collapsed"
        )
        st.session_state['etapa_projeto'] = etapa

    with col_conteudo:
        etapa = st.session_state.get('etapa_projeto')

        if etapa == "🔍 Análise do Projeto":
            st.header("🔍 Análise do Projeto", divider=True)
            tabs = st.tabs(["📑 Adequação ao Edital", "🏆 Comparativo"])

            with tabs[0]:
                if st.button("📑 Avaliar Edital"):
                    with st.spinner("Analisando..."):
                        st.session_state['analise_edital'] = avaliar_contra_edital(st.session_state['texto_projeto'])
                        st.success("✅ Análise concluída.")
                if 'analise_edital' in st.session_state:
                    st.subheader("📋 Resultado")
                    st.write(st.session_state['analise_edital'])

            with tabs[1]:
                if st.button("🏆 Comparar com Aprovados"):
                    with st.spinner("Comparando..."):
                        st.session_state['analise_comparativa'] = comparar_com_selecionados(st.session_state['texto_projeto'])
                        st.success("✅ Comparação finalizada.")
                if 'analise_comparativa' in st.session_state:
                    st.subheader("📊 Resultado")
                    st.write(st.session_state['analise_comparativa'])

        elif etapa == "📑 Gerar Documentos":
            st.header("📑 Geração de Documentos", divider=True)
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


def pagina_novo_projeto():
    st.header('✨ Crie um novo projeto')
    
    with st.form("novo_projeto_form"):
        nome = st.text_input("Nome do Projeto")
        descricao = st.text_area("Descrição")
        categoria = st.selectbox("Categoria", ["Artes", "Música", "Teatro"])
        
        if st.form_submit_button("Salvar Projeto"):
            st.session_state['projeto'] = {
                'nome': nome,
                'descricao': descricao,
                'categoria': categoria
            }
            st.success("Projeto criado com sucesso!")

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
        st.stop()  # Impede renderização dupla
    
    # Páginas autenticadas
    if 'fluxo' not in st.session_state:
        pagina_inicial()
    else:
        if st.session_state['fluxo'] == 'projeto_existente':
            pagina_projeto_existente()
        elif st.session_state['fluxo'] == 'novo_projeto':
            pagina_novo_projeto()

if __name__ == '__main__':
    main()