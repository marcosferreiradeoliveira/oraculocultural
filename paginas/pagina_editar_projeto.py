import tempfile
import streamlit as st
import firebase_admin
from firebase_admin import firestore, credentials
from models import (
    get_llm,
    gerar_resumo_projeto,
    gerar_orcamento,
    gerar_cronograma,
    gerar_objetivos,
    gerar_justificativa,
    gerar_etapas_trabalho,
    gerar_ficha_tecnica
    
)
from loaders import carrega_pdf
from analise import (
    avaliar_contra_edital,
    comparar_com_selecionados
)
import re

llm = get_llm()


def pagina_editar_projeto():
    """Página de edição com menu lateral de 3 seções"""
    
    # CSS para controlar a exibição do sidebar
    st.markdown("""
    <style>
        /* Garante que a sidebar esteja sempre visível */
        section[data-testid="stSidebar"] {
            min-width: 250px !important;
            width: 250px !important;
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            transform: none !important;
        }

        /* Esconde o botão de recolher */
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)


    # Inicializa o Firestore se ainda não estiver inicializado
    try:
        if not firebase_admin._apps:
            cred = credentials.Certificate("config/firebase-service-account.json")
            firebase_admin.initialize_app(cred)
        db = firestore.client()
    except Exception as e:
        st.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        return

    # Verificação de autenticação e projeto selecionado
    if 'user' not in st.session_state:
        st.error("Por favor, faça login primeiro")
        return

    projeto = st.session_state.get('projeto_selecionado', {})
    if not projeto:
        st.error("Nenhum projeto selecionado")
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun()

    # Menu Lateral
    with st.sidebar:
        st.title("📂 Menu de Edição")
        seção = st.radio(
            "Selecione a seção:",
            ["📥 Carregar Projeto", "🔍 Fazer Diagnóstico", "📄 Gerar Documentos"],
            index=0
        )
        
        st.divider()
        if st.button("⬅️ Voltar para Projetos"):
            st.session_state['pagina_atual'] = 'projetos'
            st.rerun()

    # Título da página
    st.title(f"✏️ Editando: {projeto.get('nome', 'Projeto sem nome')}")

   # Seção 1: Carregar Projeto
    if seção == "📥 Carregar Projeto":
        st.header("Carregar Conteúdo do Projeto")

        texto_existente = projeto.get('texto_projeto', '')
        texto_input = texto_existente 
        texto_limpo = re.sub(r'\n+', '\n\n', texto_input.strip())  # Normaliza várias quebras seguidas
 # Inicialmente mostra o que já existe

        if texto_existente:
            st.success("📄 Conteúdo do projeto já existente carregado.")
        else:
            st.info("Nenhum conteúdo existente foi encontrado.")

        st.subheader("🧾 Inserir ou editar conteúdo do projeto")
        modo_entrada = st.radio("Escolha a forma de entrada:", ["✍️ Digitar texto", "📄 Importar PDF"], horizontal=True)

        if modo_entrada == "✍️ Digitar texto":
            texto_input = st.text_area("Digite ou edite o conteúdo do projeto:", value=texto_existente, height=300, key="caixa_texto_manual")
        elif modo_entrada == "📄 Importar PDF":
            arquivo = st.file_uploader("Selecione o arquivo PDF", type=["pdf"], key="pdf_uploader_novo")
            if arquivo:
                with tempfile.NamedTemporaryFile(suffix=".pdf") as temp:
                    temp.write(arquivo.read())
                    try:
                        texto_input = carrega_pdf(temp.name)
                        st.success("✅ PDF carregado com sucesso!")
                        st.text_area("Conteúdo extraído do PDF", texto_limpo, height=200, key="visualizacao_pdf")
                    except Exception as e:
                        st.error(f"Erro ao processar PDF: {str(e)}")

        if st.button("💾 Salvar Conteúdo no Projeto"):
            if texto_input.strip():
                try:
                    db.collection('projetos').document(projeto['id']).update({
                        'texto_projeto': texto_input,
                        'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                    })
                    st.session_state['texto_projeto'] = texto_input
                    st.success("✅ Conteúdo do projeto salvo com sucesso!")
                except Exception as e:
                    st.error(f"Erro ao salvar conteúdo: {str(e)}")
            else:
                st.warning("Por favor, forneça um conteúdo antes de salvar.")


    # Seção 2: Fazer Diagnóstico
    elif seção == "🔍 Fazer Diagnóstico":
        st.header("Diagnóstico do Projeto")
        
        texto_projeto = st.session_state.get('texto_projeto') or projeto.get('texto_projeto', '')
        texto_projeto = texto_projeto.strip()
        if not texto_projeto:
            st.warning("⚠️ Por favor, carregue um PDF na seção 'Carregar PDF'.")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Análise Automática")
                if st.button("Executar Diagnóstico Completo", key="btn_diagnostico"):
                    with st.spinner("Analisando projeto com base no edital e projetos aprovados..."):
                        try:
                            analise_edital = avaliar_contra_edital(texto_projeto)
                            comparativo = comparar_com_selecionados(texto_projeto)

                            diagnostico_texto = f"{analise_edital}\n\n{comparativo}"

                            db.collection('projetos').document(projeto['id']).update({
                                'diagnostico_texto': diagnostico_texto,
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })

                            st.session_state['diagnostico_texto'] = diagnostico_texto
                            st.success("✅ Diagnóstico concluído e salvo!")
                        except Exception as e:
                            st.error(f"Erro ao gerar diagnóstico: {str(e)}")

            # with col2:
            #     st.subheader("Diagnóstico Manual")
            #     anotacoes = st.text_area(
            #         "Anotações e observações",
            #         value=projeto.get('anotacoes', ''),
            #         height=200,
            #         key="anotacoes_diagnostico"
            #     )

            #     if st.button("Salvar Anotações", key="btn_salvar_anotacoes"):
            #         try:
            #             db.collection('projetos').document(projeto['id']).update({
            #                 'anotacoes': anotacoes,
            #                 'ultima_atualizacao': firestore.SERVER_TIMESTAMP
            #             })
            #             st.success("Anotações salvas no projeto!")
            #         except Exception as e:
            #             st.error(f"Erro ao salvar anotações: {str(e)}")

            st.divider()
            st.subheader("📋 Resultado do Diagnóstico")

            texto_diagnostico = st.session_state.get('diagnostico_texto', projeto.get('diagnostico_texto', ''))
            if texto_diagnostico:
                st.text_area("Diagnóstico completo gerado", value=texto_diagnostico, height=400, disabled=True)
            else:
                st.info("Nenhum diagnóstico gerado ainda.")

    # Seção 3: Gerar Documentos
    elif seção == "📄 Gerar Documentos":
        st.header("Gerar Documentos para o Projeto")

        if 'texto_projeto' not in st.session_state and 'texto_projeto' not in projeto:
            st.warning("⚠️ Por favor, carregue um conteúdo na seção 'Carregar Projeto'")
        else:
            texto = st.session_state.get('texto_projeto', projeto.get('texto_projeto', ''))
            diagnostico = projeto.get('diagnostico_texto', '')

            tipos = {
                "Resumo Executivo": "resumo_executivo",
                "Cronograma Detalhado": "cronograma_detalhado",
                "Orçamento Completo": "orcamento_completo",
                "Justificativa Técnica": "justificativa_tecnica",
                "Objetivos SMART": "objetivos_smart",
                "Etapas de Trabalho": "etapas_trabalho",
                "Ficha Técnica": "ficha_tecnica"
            }

            tipo_selecionado = st.selectbox("Selecione o tipo de documento:", list(tipos.keys()), key="sel_tipo_documento")
            chave = tipos[tipo_selecionado]

            if st.button(f"Gerar {tipo_selecionado}", key=f"btn_gerar_{chave}"):
                with st.spinner(f"Gerando {tipo_selecionado}..."):
                    try:
                        llm = get_llm()
                        func_map = {
                            "resumo_executivo": gerar_resumo_projeto,
                            "cronograma_detalhado": gerar_cronograma,
                            "orcamento_completo": gerar_orcamento,
                            "justificativa_tecnica": gerar_justificativa,
                            "objetivos_smart": gerar_objetivos,
                            "etapas_trabalho": gerar_etapas_trabalho,
                            "ficha_tecnica": gerar_ficha_tecnica
                        }

                        documento = func_map[chave](texto, diagnostico, llm)
                        st.session_state[chave] = documento
                        st.success(f"{tipo_selecionado} gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar documento: {str(e)}")

            if chave in st.session_state:
                st.divider()
                st.subheader(f"📝 {tipo_selecionado}")
                st.text_area("Conteúdo gerado", st.session_state[chave], height=300, key=f"area_{chave}")

                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="⏬ Baixar Documento",
                        data=st.session_state[chave],
                        file_name=f"{chave}.txt",
                        mime="text/plain",
                        key=f"btn_download_{chave}"
                    )
                with col2:
                    if st.button("Salvar no Projeto", key=f"btn_salvar_{chave}"):
                        try:
                            db.collection('projetos').document(projeto['id']).update({
                                f'documentos.{chave}': st.session_state[chave],
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            st.success("Documento salvo no projeto!")
                        except Exception as e:
                            st.error(f"Erro ao salvar documento: {str(e)}")


