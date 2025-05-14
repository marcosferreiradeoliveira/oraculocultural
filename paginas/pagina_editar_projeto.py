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
    gerar_justificativa
)
from loaders import carrega_pdf
import re


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
        
        if 'texto_projeto' not in st.session_state:
            st.warning("Por favor, carregue um PDF na seção 'Carregar PDF'")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Análise Automática")
                if st.button("Executar Diagnóstico Completo", key="btn_diagnostico"):
                    with st.spinner("Analisando projeto..."):
                        try:
                            diagnostico = {
                                'pontos_fortes': [
                                    "Proposta bem estruturada",
                                    "Objetivos claros e mensuráveis",
                                    "Público-alvo bem definido"
                                ],
                                'melhorias': [
                                    "Cronograma precisa de mais detalhes",
                                    "Orçamento pode ser mais realista",
                                    "Falta justificativa técnica mais robusta"
                                ]
                            }
                            
                            # Salva o diagnóstico no Firestore
                            db.collection('projetos').document(projeto['id']).update({
                                'diagnostico': diagnostico,
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            
                            st.session_state['diagnostico'] = diagnostico
                            st.success("Diagnóstico concluído e salvo!")
                        except Exception as e:
                            st.error(f"Erro ao gerar diagnóstico: {str(e)}")
            
            with col2:
                st.subheader("Diagnóstico Manual")
                anotacoes = st.text_area("Anotações e observações", 
                                       value=projeto.get('anotacoes', ''),
                                       height=200,
                                       key="anotacoes_diagnostico")
                
                if st.button("Salvar Anotações", key="btn_salvar_anotacoes"):
                    try:
                        db.collection('projetos').document(projeto['id']).update({
                            'anotacoes': anotacoes,
                            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                        })
                        st.success("Anotações salvas no projeto!")
                    except Exception as e:
                        st.error(f"Erro ao salvar anotações: {str(e)}")
            
            # Mostra diagnóstico existente se disponível
            if 'diagnostico' in st.session_state or 'diagnostico' in projeto:
                diagnostico = st.session_state.get('diagnostico', projeto.get('diagnostico', {}))
                
                st.divider()
                st.subheader("Resultados do Diagnóstico")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("✅ **Pontos Fortes**")
                    for item in diagnostico.get('pontos_fortes', []):
                        st.markdown(f"- {item}")
                
                with col_b:
                    st.markdown("⚠️ **Sugestões de Melhoria**")
                    for item in diagnostico.get('melhorias', []):
                        st.markdown(f"- {item}")

    # Seção 3: Gerar Documentos
    elif seção == "📄 Gerar Documentos":
        st.header("Gerar Documentos para o Projeto")
        
        if 'texto_projeto' not in st.session_state and 'texto_projeto' not in projeto:
            st.warning("Por favor, carregue um PDF na seção 'Carregar PDF'")
        else:
            texto = st.session_state.get('texto_projeto', projeto.get('texto_projeto', ''))
            
            tipo_documento = st.selectbox(
                "Selecione o tipo de documento:",
                [
                    "Resumo Executivo", 
                    "Cronograma Detalhado", 
                    "Orçamento Completo", 
                    "Justificativa Técnica",
                    "Objetivos SMART"
                ],
                key="sel_tipo_documento"
            )
            
            if st.button(f"Gerar {tipo_documento}", key=f"btn_gerar_{tipo_documento}"):
                with st.spinner(f"Gerando {tipo_documento}..."):
                    try:
                        llm = get_llm()
                        if tipo_documento == "Resumo Executivo":
                            documento = gerar_resumo_projeto(llm, texto)
                        elif tipo_documento == "Cronograma Detalhado":
                            documento = gerar_cronograma(llm, texto)
                        elif tipo_documento == "Orçamento Completo":
                            documento = gerar_orcamento(llm, texto)
                        elif tipo_documento == "Justificativa Técnica":
                            documento = gerar_justificativa(llm, texto)
                        elif tipo_documento == "Objetivos SMART":
                            documento = gerar_objetivos(llm, texto)
                        
                        st.session_state['documento_gerado'] = documento
                        st.success(f"{tipo_documento} gerado com sucesso!")
                    except Exception as e:
                        st.error(f"Erro ao gerar documento: {str(e)}")
            
            if 'documento_gerado' in st.session_state:
                st.divider()
                st.subheader(f"📝 {tipo_documento}")
                st.text_area("Conteúdo gerado", st.session_state['documento_gerado'], height=300, key="area_documento")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="⏬ Baixar Documento",
                        data=st.session_state['documento_gerado'],
                        file_name=f"{tipo_documento.replace(' ', '_')}.txt",
                        mime="text/plain",
                        key="btn_download_doc"
                    )
                with col2:
                    if st.button("Salvar no Projeto", key="btn_salvar_doc"):
                        try:
                            doc_ref = db.collection('projetos').document(projeto['id'])
                            doc_ref.update({
                                f'documentos.{tipo_documento.replace(" ", "_").lower()}': st.session_state['documento_gerado'],
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            st.success("Documento salvo no projeto!")
                        except Exception as e:
                            st.error(f"Erro ao salvar documento: {str(e)}")