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
        section[data-testid="stSidebar"] {
            min-width: 250px !important;
            width: 250px !important;
        }
        [data-testid="collapsedControl"] {
            display: none !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Inicializa o Firestore
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
        texto_limpo = re.sub(r'\n+', '\n\n', texto_input.strip())

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

            # Mapeamento de tipos de documentos
            tipos_documentos = {
                "Resumo Executivo": ("resumo_executivo", gerar_resumo_projeto),
                "Cronograma Detalhado": ("cronograma_detalhado", gerar_cronograma),
                "Orçamento Completo": ("orcamento_completo", gerar_orcamento),
                "Justificativa Técnica": ("justificativa_tecnica", gerar_justificativa),
                "Objetivos SMART": ("objetivos_smart", gerar_objetivos),
                "Etapas de Trabalho": ("etapas_trabalho", gerar_etapas_trabalho),
                "Ficha Técnica": ("ficha_tecnica", gerar_ficha_tecnica)
            }

            # Seleção do tipo de documento
            tipo_selecionado = st.selectbox(
                "Selecione o tipo de documento:", 
                list(tipos_documentos.keys()), 
                key="sel_tipo_documento"
            )
            
            # Obter chave e função correspondente
            chave, funcao_geradora = tipos_documentos[tipo_selecionado]
            
            # Verificar se já existe documento no Firebase
            doc_ref = db.collection('projetos').document(projeto['id'])
            doc_snapshot = doc_ref.get()
            
            # Adicionar mais debugging
            st.write("Verificando no Firestore...")
            
            documento_existente = None
            if doc_snapshot.exists:
                projeto_data = doc_snapshot.to_dict()
                
                # Exibir estrutura do documento para debugging
                st.write("Documento encontrado no Firestore.")
                st.write("Campos disponíveis:", ", ".join(projeto_data.keys()))
                
                if 'documentos' in projeto_data:
                    st.write("Campo 'documentos' encontrado com as chaves:", ", ".join(projeto_data['documentos'].keys() if projeto_data['documentos'] else []))
                    
                    if chave in projeto_data['documentos']:
                        documento_existente = projeto_data['documentos'][chave]
                        st.success(f"✅ Documento '{tipo_selecionado}' encontrado no banco de dados!")
                    else:
                        st.info(f"Chave '{chave}' não encontrada dentro do campo 'documentos'")
                else:
                    st.info("Campo 'documentos' não encontrado no projeto do Firestore")
            else:
                st.warning(f"Documento com ID {projeto['id']} não encontrado no Firestore")
            
            # Exibir valor atual em session_state e projeto local
            if st.checkbox("Mostrar dados detalhados para debug", value=False):
                st.write("ID do projeto:", projeto.get('id'))
                if 'documentos' in projeto:
                    st.write("Documentos no objeto projeto em memória:")
                    for k, v in projeto.get('documentos', {}).items():
                        st.write(f"- {k}: {v[:100]}..." if v and len(v) > 100 else f"- {k}: {v}")
                else:
                    st.write("Nenhum campo 'documentos' no objeto projeto em memória")
            
            # Exibir documento existente ou opção para gerar novo
            if documento_existente:
                st.subheader(f"📄 {tipo_selecionado} Existente")
                st.text_area("Conteúdo do documento", 
                           value=documento_existente, 
                           height=300,
                           key=f"view_{chave}")
                
                # Opções para o documento existente
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="⏬ Baixar Documento",
                        data=documento_existente,
                        file_name=f"{chave}.txt",
                        mime="text/plain",
                        key=f"dl_{chave}"
                    )
                with col2:
                    if st.button("🔄 Gerar Nova Versão", key=f"new_{chave}"):
                        with st.spinner(f"Gerando novo {tipo_selecionado}..."):
                            try:
                                novo_documento = funcao_geradora(texto, context=diagnostico, llm=llm)
                                st.session_state[chave] = novo_documento
                                st.success("Novo documento gerado com sucesso!")
                            except Exception as e:
                                st.error(f"Erro ao gerar documento: {str(e)}")
            else:
                st.info(f"Nenhum documento '{tipo_selecionado}' encontrado no projeto.")
                
                if st.button(f"✨ Gerar {tipo_selecionado}", key=f"gen_{chave}"):
                    with st.spinner(f"Gerando {tipo_selecionado}..."):
                        try:
                            novo_documento = funcao_geradora(texto, context=diagnostico, llm=llm)
                            st.session_state[chave] = novo_documento
                            st.success("Documento gerado com sucesso!")
                        except Exception as e:
                            st.error(f"Erro ao gerar documento: {str(e)}")

            # Se há um documento novo na sessão (gerado ou carregado)
            if chave in st.session_state:
                st.subheader(f"📝 Visualização do {tipo_selecionado}")
                st.text_area("Conteúdo do documento", 
                           value=st.session_state[chave], 
                           height=300,
                           key=f"edit_{chave}")
                
                # Opções para salvar o novo documento
                if st.button("💾 Salvar no Projeto", key=f"save_{chave}"):
                    try:
                        # Atualiza o documento específico mantendo outros existentes
                        update_data = {
                            f'documentos.{chave}': st.session_state[chave],
                            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                        }
                        
                        doc_ref.update(update_data)
                        st.success("Documento salvo com sucesso no projeto!")
                    except Exception as e:
                        st.error(f"Erro ao salvar documento: {str(e)}")


