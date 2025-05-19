import tempfile
import streamlit as st
import traceback
import time
import firebase_admin
from firebase_admin import firestore, credentials
from services.firebase_init import initialize_firebase, get_error_message
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
import os

llm = get_llm() # LLM global instanciada

def slugify(text):
    if not text: return ""
    text = text.replace(' ', '_')
    text = re.sub(r'[^\w_]', '', text) # Remove non-alphanumeric (except underscore)
    return text.lower()

def pagina_editar_projeto():
    """Página de edição com menu lateral de 3 seções"""
    
    st.markdown("""
    <style>
        section[data-testid="stSidebar"] {
            min-width: 250px !important;
            width: 250px !important;
            visibility: visible !important;
            transform: none !important;
        }
        section[data-testid="stSidebar"] > div {padding-top: 2rem;}
        section[data-testid="stSidebar"] > div > div {padding-top: 2rem;}
        div[data-testid="collapsedControl"] {display: none !important;}
    </style>
    """, unsafe_allow_html=True)

    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                st.sidebar.error(get_error_message())
                return
        db = firestore.client()
        st.sidebar.success("Conexão com Firebase estabelecida!")
    except Exception as e:
        st.sidebar.error(f"Erro ao conectar com o banco de dados: {str(e)}")
        return

    if 'user' not in st.session_state:
        st.error("Por favor, faça login primeiro")
        return

    projeto = st.session_state.get('projeto_selecionado', {})
    if not projeto:
        st.error("Nenhum projeto selecionado")
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun()
    
    projeto_id = projeto.get('id', 'default_id') # Garante que temos um ID

    with st.sidebar:
        st.title("📂 Menu de Edição")
        if 'secao_atual' not in st.session_state:
            st.session_state['secao_atual'] = "📥 Carregar Projeto"
            
        secao_selecionada = st.radio(
            "Selecione a seção:",
            ["📥 Carregar Projeto", "🔍 Fazer Diagnóstico", "📄 Gerar Documentos"],
            index=["📥 Carregar Projeto", "🔍 Fazer Diagnóstico", "📄 Gerar Documentos"].index(st.session_state['secao_atual']),
            key=f'secao_radio_{projeto_id}' 
        )
        
        if secao_selecionada != st.session_state['secao_atual']:
            st.session_state['secao_atual'] = secao_selecionada
            st.rerun()
        
        st.divider()
        if st.button("⬅️ Voltar para Projetos"):
            st.session_state['pagina_atual'] = 'projetos'
            # Limpar estados específicos da página de edição ao sair
            keys_to_clear = [k for k in st.session_state.keys() if projeto_id in k or 'diagnostico_editavel' in k or 'doc_gerado' in k]
            for key in keys_to_clear:
                del st.session_state[key]
            st.rerun()

    st.title(f"✏️ Editando: {projeto.get('nome', 'Projeto sem nome')}")

    # --- Seção 1: Carregar Projeto ---
    if st.session_state['secao_atual'] == "📥 Carregar Projeto":
        st.header("Carregar Conteúdo do Projeto")

        if 'ultimas_alteracoes' in st.session_state and st.session_state['ultimas_alteracoes']['projeto_id'] == projeto_id:
            st.success("✅ Alterações aplicadas com sucesso!")
            st.subheader("Detalhes da última alteração:")
            st.write(st.session_state['ultimas_alteracoes']['alteracoes'])
            del st.session_state['ultimas_alteracoes']

        texto_inicial_textarea = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', ''))

        # Initialize current_texto_input for the specific project if not set or project changed
        if st.session_state.get(f'current_texto_input_pid') != projeto_id:
            st.session_state[f'current_texto_input_{projeto_id}'] = texto_inicial_textarea
            st.session_state[f'current_texto_input_pid'] = projeto_id

        if texto_inicial_textarea:
            st.success("📄 Conteúdo do projeto já existente carregado.")
        else:
            st.info("Nenhum conteúdo existente foi encontrado para este projeto.")

        st.subheader("🧾 Inserir ou editar conteúdo do projeto")
        modo_entrada = st.radio("Escolha a forma de entrada:", ["✍️ Digitar texto", "📄 Importar PDF"], horizontal=True, key=f"modo_entrada_{projeto_id}")

        if modo_entrada == "✍️ Digitar texto":
            texto_digitado = st.text_area("Digite ou edite o conteúdo do projeto:", 
                                       value=st.session_state.get(f'current_texto_input_{projeto_id}', texto_inicial_textarea), 
                                       height=300, 
                                       key=f"caixa_texto_manual_{projeto_id}")
            if texto_digitado != st.session_state.get(f'current_texto_input_{projeto_id}'):
                st.session_state[f'current_texto_input_{projeto_id}'] = texto_digitado

        elif modo_entrada == "📄 Importar PDF":
            # Adiciona informações sobre limites de tamanho
            st.info("""
            📝 **Dicas para importação de PDF:**
            - Tamanho máximo recomendado: 10MB
            - Para arquivos maiores, considere dividir em partes menores
            - Certifique-se que o PDF não está protegido por senha
            - O texto deve estar selecionável (não apenas imagens)
            """)
            
            arquivo = st.file_uploader("Selecione o arquivo PDF", type=["pdf"], key=f"pdf_uploader_novo_{projeto_id}")
            
            if arquivo:
                # Verifica o tamanho do arquivo
                tamanho_arquivo = arquivo.size / (1024 * 1024)  # Converte para MB
                if tamanho_arquivo > 10:
                    st.warning(f"⚠️ O arquivo é muito grande ({tamanho_arquivo:.1f}MB). Recomendamos dividir em partes menores para melhor processamento.")
                    if not st.checkbox("Continuar mesmo assim", key=f"continuar_pdf_grande_{projeto_id}"):
                        st.stop()

                with st.spinner("Processando PDF... Isso pode levar alguns instantes para arquivos maiores."):
                    try:
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                            temp.write(arquivo.read())
                            temp_path = temp.name

                        try:
                            texto_input_pdf = carrega_pdf(temp_path)
                            if not texto_input_pdf or len(texto_input_pdf.strip()) < 10:
                                st.error("⚠️ O PDF não parece conter texto extraível. Verifique se o arquivo não está apenas com imagens ou se o texto está selecionável.")
                            else:
                                st.session_state[f'current_texto_input_{projeto_id}'] = texto_input_pdf
                                st.success(f"✅ PDF carregado com sucesso! ({len(texto_input_pdf)} caracteres extraídos)")
                                st.text_area("Conteúdo extraído do PDF (visualização)", 
                                        value=st.session_state[f'current_texto_input_{projeto_id}'], 
                                        height=200, 
                                        key=f"visualizacao_pdf_{projeto_id}", 
                                        disabled=True)
                                st.info("Para editar o conteúdo do PDF, selecione 'Digitar texto' e o conteúdo será copiado para a caixa de edição.")
                        except Exception as e:
                            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
                            if "password" in str(e).lower():
                                st.error("O PDF parece estar protegido por senha. Por favor, remova a proteção e tente novamente.")
                            elif "400" in str(e):
                                st.error("Erro ao processar o PDF. O arquivo pode estar corrompido ou em formato não suportado.")
                            st.code(traceback.format_exc())
                        finally:
                            # Limpa o arquivo temporário
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                    except Exception as e:
                        st.error(f"Erro ao processar PDF: {str(e)}")
                        st.code(traceback.format_exc())
        
        texto_para_salvar = st.session_state.get(f'current_texto_input_{projeto_id}', '')

        if st.button("💾 Salvar Conteúdo no Projeto", key=f"salvar_conteudo_{projeto_id}"):
            if texto_para_salvar.strip():
                try:
                    doc_ref = db.collection('projetos').document(projeto_id)
                    current_doc = doc_ref.get()
                    if current_doc.exists:
                        current_firebase_text = current_doc.to_dict().get('texto_projeto', '').strip()
                        
                        if current_firebase_text == texto_para_salvar.strip():
                            st.warning("Conteúdo no Firebase é idêntico ao conteúdo a ser salvo. Nenhuma alteração será feita no BD.")
                        else:
                            doc_ref.update({
                                'texto_projeto': texto_para_salvar.strip(),
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            # Update local session state for texto_projeto as well
                            st.session_state[f'texto_projeto_{projeto_id}'] = texto_para_salvar.strip()
                            # Update the main project object in session if it's there
                            if 'projeto_selecionado' in st.session_state and st.session_state['projeto_selecionado']['id'] == projeto_id:
                                st.session_state['projeto_selecionado']['texto_projeto'] = texto_para_salvar.strip()
                        st.success("✅ Conteúdo do projeto salvo com sucesso!")
                        time.sleep(1)
                        st.rerun() 
                    else:
                        st.error("Erro: Projeto não encontrado no Firebase para salvar.")
                except Exception as e:
                    st.error(f"Erro ao salvar conteúdo: {str(e)}")
                    st.code(traceback.format_exc()) 
            else:
                st.warning("Por favor, forneça um conteúdo antes de salvar.")

    # --- Seção 2: Fazer Diagnóstico ---
    elif st.session_state['secao_atual'] == "🔍 Fazer Diagnóstico":
        st.header("Diagnóstico do Projeto e Melhorias com IA")
        
        texto_projeto_atual = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', '')).strip()
        
        if not texto_projeto_atual:
            st.warning("⚠️ Por favor, carregue ou salve um conteúdo na seção 'Carregar Projeto' primeiro.")
        else:
            st.subheader("Análise Automática")
            if st.button("Executar Diagnóstico Completo", key=f"btn_diagnostico_{projeto_id}"):
                # Clear previous editable diagnosis when new one is generated
                if f'diagnostico_editavel_{projeto_id}' in st.session_state:
                    del st.session_state[f'diagnostico_editavel_{projeto_id}']

                with st.spinner("Analisando projeto com base no edital e projetos aprovados..."):
                    try:
                        diagnostico_container = st.empty()
                        diagnostico_texto_stream = ""
                        def update_diagnostico_stream(text):
                            nonlocal diagnostico_texto_stream
                            diagnostico_texto_stream += text
                            diagnostico_container.markdown(diagnostico_texto_stream)
                        
                        # Buscar informações do edital associado no Firestore
                        edital_associado_id = projeto.get('edital_associado')
                        texto_edital_context = None
                        texto_selecionados_context = None

                        if edital_associado_id:
                            try:
                                edital_doc = db.collection('editais').document(edital_associado_id).get()
                                if edital_doc.exists:
                                    edital_data = edital_doc.to_dict()
                                    texto_edital_context = edital_data.get('texto_edital', '')
                                    texto_selecionados_context = edital_data.get('texto_selecionados', '')
                                    
                                    if not texto_edital_context:
                                        st.warning("O edital associado não possui texto para análise.")
                                    else:
                                        st.info(f"Analisando projeto contra o edital: {edital_data.get('nome', 'Edital sem nome')}")
                                else:
                                    st.warning("Edital associado não encontrado no banco de dados.")
                            except Exception as e:
                                st.error(f"Erro ao buscar edital: {str(e)}")
                                st.code(traceback.format_exc())
                        else:
                            st.info("Nenhum edital associado a este projeto. A análise será feita apenas com base no texto do projeto.")

                        # Gerar diagnóstico com os contextos obtidos
                        analise_edital_stream = avaliar_contra_edital(texto_projeto_atual, texto_edital_context, texto_selecionados_context)
                        for char in analise_edital_stream: 
                            update_diagnostico_stream(char)
                            time.sleep(0.005)
                        
                        update_diagnostico_stream("\n\n")
                        
                        comparativo_stream = comparar_com_selecionados(texto_projeto_atual, texto_edital_context, texto_selecionados_context)
                        for char in comparativo_stream: 
                            update_diagnostico_stream(char)
                            time.sleep(0.005)
                        
                        diagnostico_final_completo = diagnostico_texto_stream 

                        # Salvar diagnóstico no Firestore
                        db.collection('projetos').document(projeto_id).update({
                            'diagnostico_texto': diagnostico_final_completo,
                            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                        })
                        
                        # Atualizar estados da sessão
                        st.session_state[f'diagnostico_texto_{projeto_id}'] = diagnostico_final_completo
                        if 'projeto_selecionado' in st.session_state and st.session_state['projeto_selecionado']['id'] == projeto_id:
                            st.session_state['projeto_selecionado']['diagnostico_texto'] = diagnostico_final_completo
                        
                        st.success("✅ Diagnóstico concluído e salvo!")
                        time.sleep(1)
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar diagnóstico: {str(e)}")
                        st.code(traceback.format_exc())

            st.divider()
            st.subheader("Resultado do Diagnóstico (Editável)")

            texto_diagnostico_atual_db = st.session_state.get(f'diagnostico_texto_{projeto_id}', projeto.get('diagnostico_texto', ''))
            
            # Inicializa o diagnóstico editável na sessão se ainda não existir ou se mudou
            if f'diagnostico_editavel_{projeto_id}' not in st.session_state or st.session_state.get(f'diagnostico_editavel_base_{projeto_id}') != texto_diagnostico_atual_db:
                st.session_state[f'diagnostico_editavel_{projeto_id}'] = texto_diagnostico_atual_db
                st.session_state[f'diagnostico_editavel_base_{projeto_id}'] = texto_diagnostico_atual_db


            if texto_diagnostico_atual_db or st.session_state.get(f'diagnostico_editavel_{projeto_id}'):
                diagnostico_para_editar = st.text_area(
                    "Edite o diagnóstico abaixo conforme necessário:", 
                    value=st.session_state.get(f'diagnostico_editavel_{projeto_id}', ''), 
                    height=300, 
                    key=f"diagnostico_edit_area_{projeto_id}"
                )
                # Atualiza a sessão se houver mudança
                if diagnostico_para_editar != st.session_state.get(f'diagnostico_editavel_{projeto_id}'):
                    st.session_state[f'diagnostico_editavel_{projeto_id}'] = diagnostico_para_editar
                    # Não precisa de rerun aqui, o botão de salvar cuidará disso.

                if st.button("💾 Salvar Diagnóstico Editado", key=f"salvar_diag_editado_{projeto_id}"):
                    diagnostico_salvar = st.session_state.get(f'diagnostico_editavel_{projeto_id}', '').strip()
                    if diagnostico_salvar:
                        try:
                            db.collection('projetos').document(projeto_id).update({
                                'diagnostico_texto': diagnostico_salvar,
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            })
                            st.session_state[f'diagnostico_texto_{projeto_id}'] = diagnostico_salvar
                            st.session_state[f'diagnostico_editavel_base_{projeto_id}'] = diagnostico_salvar # Atualiza base para comparação futura
                            if 'projeto_selecionado' in st.session_state and st.session_state['projeto_selecionado']['id'] == projeto_id:
                                st.session_state['projeto_selecionado']['diagnostico_texto'] = diagnostico_salvar
                            st.success("✅ Diagnóstico editado salvo com sucesso!")
                            time.sleep(1); st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar diagnóstico editado: {str(e)}"); st.code(traceback.format_exc())
                    else:
                        st.warning("Diagnóstico está vazio. Nada para salvar.")
                
                st.markdown("---")
                st.subheader("🤖 Aplicar Melhorias no Texto do Projeto com IA (usando o diagnóstico acima)")
                st.markdown("""
                A IA tentará incorporar as sugestões e melhorias do diagnóstico (editado ou original) de forma integrada no texto original do projeto.
                **Atenção:** O texto original do projeto será substituído pela versão revisada.
                """)

                diagnostico_para_aplicar = st.session_state.get(f'diagnostico_editavel_{projeto_id}', texto_diagnostico_atual_db)

                if st.button("✨ Revisar Texto do Projeto Usando o Diagnóstico Acima", key=f"aplicar_diagnostico_llm_{projeto_id}"):
                    if not diagnostico_para_aplicar.strip():
                        st.warning("O diagnóstico está vazio. Não é possível aplicar melhorias.")
                    else:
                        with st.spinner("IA trabalhando para refinar seu projeto... Por favor, aguarde."):
                            # (Lógica de revisão do texto do projeto pela LLM com base no diagnóstico_para_aplicar)
                            try:
                                # ... (prompt e chamada LLM como na versão anterior, usando 'diagnostico_para_aplicar') ...
                                prompt_template_revisao = """
Você é um editor especialista em aprimorar propostas de projetos e editais.
Sua tarefa é revisar e reescrever o TEXTO ORIGINAL DO PROJETO abaixo. Utilize o DIAGNÓSTICO DO PROJETO fornecido como um guia detalhado para identificar áreas de melhoria.
Incorpore de forma coesa e integrada as sugestões, correções e pontos de aprimoramento apontados no DIAGNÓSTICO.
O objetivo é produzir uma nova versão do TEXTO ORIGINAL DO PROJETO que esteja significativamente melhorada, mais clara, completa, persuasiva e alinhada com as recomendações do DIAGNÓSTICO.
Mantenha o tom e o escopo essenciais do projeto, a menos que o DIAGNÓSTICO sugira alterações explícitas nesses aspectos. Se o DIAGNÓSTICO não contiver sugestões aplicáveis ou se o TEXTO ORIGINAL DO PROJETO já for excelente e não necessitar de alterações com base no DIAGNÓSTICO, retorne o TEXTO ORIGINAL DO PROJETO inalterado.
Certifique-se de retornar APENAS o texto do projeto revisado e aprimorado. Não inclua preâmbulos, saudações, comentários ou qualquer metadiscurso.
[TEXTO ORIGINAL DO PROJETO]:\n{texto_original}\n\n[DIAGNÓSTICO DO PROJETO]:\n{texto_diagnostico}\n\n[TEXTO DO PROJETO REVISADO E APRIMORADO]:"""
                                prompt_revisao = prompt_template_revisao.format(
                                    texto_original=texto_projeto_atual,
                                    texto_diagnostico=diagnostico_para_aplicar
                                )
                                response_revisao = llm.invoke(prompt_revisao) 
                                texto_projeto_revisado = (response_revisao.content if hasattr(response_revisao, 'content') else str(response_revisao)).strip()

                                if not texto_projeto_revisado: st.error("A IA não retornou um texto revisado."); return

                                db.collection('projetos').document(projeto_id).update({
                                    'texto_projeto': texto_projeto_revisado,
                                    'ultima_atualizacao': firestore.SERVER_TIMESTAMP,
                                    'diagnostico_aplicado_em_revisao': diagnostico_para_aplicar
                                })
                                st.session_state[f'texto_projeto_{projeto_id}'] = texto_projeto_revisado
                                if 'projeto_selecionado' in st.session_state and st.session_state['projeto_selecionado']['id'] == projeto_id:
                                    st.session_state['projeto_selecionado']['texto_projeto'] = texto_projeto_revisado
                                st.session_state['ultimas_alteracoes'] = {
                                    'projeto_id': projeto_id,
                                    'alteracoes': "Texto do projeto revisado pela IA com base no diagnóstico.",
                                    'nome_projeto': projeto.get('nome', 'Projeto sem nome')
                                }
                                st.success("✅ Texto do projeto revisado pela IA e salvo!"); st.info("Redirecionando...");
                                time.sleep(2.5); st.session_state['secao_atual'] = "📥 Carregar Projeto"; st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao aplicar diagnóstico com IA: {str(e)}"); st.code(traceback.format_exc())
            else:
                st.info("Nenhum diagnóstico encontrado. Execute a 'Análise Automática' ou adicione/edite um diagnóstico manualmente.")

    # --- Seção 3: Gerar Documentos (Refatorada) ---
    elif st.session_state['secao_atual'] == "📄 Gerar Documentos":
        st.header("Gerar Documentos para o Projeto (Guiado pelo Edital)")

        texto_base_projeto = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', ''))
        diagnostico_base_projeto = st.session_state.get(f'diagnostico_texto_{projeto_id}', projeto.get('diagnostico_texto', ''))

        if not texto_base_projeto:
            st.warning("⚠️ Por favor, carregue/salve um conteúdo para o projeto na seção 'Carregar Projeto' antes de gerar documentos.")
            return

        edital_associado_id = projeto.get('edital_associado')
        lista_documentos_sugeridos = []
        
        # Primeiro, tentar carregar documentos sugeridos do Firestore
        try:
            doc_ref = db.collection('projetos').document(projeto_id)
            doc_snapshot = doc_ref.get()
            if doc_snapshot.exists:
                projeto_data = doc_snapshot.to_dict()
                documentos_sugeridos = projeto_data.get('documentos_sugeridos', [])
                if documentos_sugeridos:
                    lista_documentos_sugeridos = documentos_sugeridos
                    st.info(f"Documentos sugeridos pelo edital carregados do banco de dados.")
        except Exception as e:
            st.error(f"Erro ao carregar documentos sugeridos: {str(e)}")

        if edital_associado_id:
            if not lista_documentos_sugeridos:
                if st.button("🔍 Analisar Edital para Sugerir Documentos", key=f"analisar_edital_docs_{projeto_id}"):
                    with st.spinner(f"Analisando edital ID: {edital_associado_id}... Isso pode levar um momento."):
                        try:
                            edital_doc_ref = db.collection('editais').document(edital_associado_id)
                            edital_doc = edital_doc_ref.get()
                            if edital_doc.exists:
                                edital_data = edital_doc.to_dict()
                                texto_edital = edital_data.get('texto_edital', '')

                                if texto_edital:
                                    prompt_extracao_docs = f"""
Analise o TEXTO DO EDITAL a seguir para identificar os documentos e seções de projeto que são:
1. Explicitamente exigidos (obrigatórios, como anexos, declarações, etc.).
2. Fortemente sugeridos ou implícitos pela estrutura do edital.
3. Cruciais para obter uma boa pontuação, com base nos critérios de avaliação.

Liste cada nome de documento ou seção de projeto identificado em uma NOVA LINHA. Seja conciso e use nomes descritivos para os documentos (ex: 'Plano de Trabalho Detalhado', 'Orçamento Analítico', 'Cronograma Físico-Financeiro', 'Matriz de Riscos', 'Currículos da Equipe').
Não inclua números ou marcadores na lista, apenas um nome de documento por linha. Se nenhum documento específico for identificado, retorne a frase "NENHUM DOCUMENTO ESPECÍFICO IDENTIFICADO".

[TEXTO DO EDITAL]:
{texto_edital}

[LISTA DE DOCUMENTOS E SEÇÕES IMPORTANTES]:
"""
                                    response_docs = llm.invoke(prompt_extracao_docs)
                                    docs_extraidos_texto = (response_docs.content if hasattr(response_docs, 'content') else str(response_docs)).strip()
                                    
                                    if "NENHUM DOCUMENTO ESPECÍFICO IDENTIFICADO" not in docs_extraidos_texto.upper():
                                        lista_documentos_sugeridos = [line.strip() for line in docs_extraidos_texto.split('\n') if line.strip()]
                                    
                                    if lista_documentos_sugeridos:
                                        # Salvar a lista de documentos no Firestore
                                        doc_ref = db.collection('projetos').document(projeto_id)
                                        doc_ref.update({
                                            'documentos_sugeridos': lista_documentos_sugeridos,
                                            'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                                        })
                                        st.success(f"Edital analisado! {len(lista_documentos_sugeridos)} tipos de documentos/seções sugeridos e salvos no banco de dados.")
                                    else:
                                        st.warning("Não foi possível identificar documentos específicos no edital ou o edital não os detalha. Verifique o texto do edital manualmente.")
                                    st.rerun()
                                else:
                                    st.error("Texto do edital associado está vazio.")
                            else:
                                st.error(f"Edital com ID {edital_associado_id} não encontrado.")
                        except Exception as e:
                            st.error(f"Erro ao analisar edital: {str(e)}")
                            st.code(traceback.format_exc())
        else:
            st.info("Nenhum edital associado a este projeto para guiar a geração de documentos. Usando lista padrão.")

        # --- Lógica de Geração de Documentos (Dinâmica ou Padrão) ---
        opcoes_documentos_dict = {}
        usando_lista_padrao = False

        if lista_documentos_sugeridos:
            for nome_doc in lista_documentos_sugeridos:
                opcoes_documentos_dict[nome_doc] = (slugify(nome_doc), None)
        
        if not opcoes_documentos_dict:
            usando_lista_padrao = True
            st.caption("Recorrendo à lista de documentos padrão.")
            opcoes_documentos_dict = {
                "Resumo Executivo": ("resumo_executivo", gerar_resumo_projeto),
                "Cronograma Detalhado": ("cronograma_detalhado", gerar_cronograma),
                "Orçamento Completo": ("orcamento_completo", gerar_orcamento),
                "Justificativa Técnica": ("justificativa_tecnica", gerar_justificativa),
                "Objetivos SMART": ("objetivos_smart", gerar_objetivos),
                "Etapas de Trabalho": ("etapas_trabalho", gerar_etapas_trabalho),
                "Ficha Técnica": ("ficha_tecnica", gerar_ficha_tecnica)
            }

        if not opcoes_documentos_dict:
            st.error("Nenhuma opção de documento disponível.")
            return

        tipo_selecionado_nome = st.selectbox(
            "Selecione o tipo de documento para gerar/visualizar:", 
            list(opcoes_documentos_dict.keys()), 
            key=f"sel_tipo_documento_dinamico_{projeto_id}"
        )

        if tipo_selecionado_nome:
            chave_doc_selecionado, funcao_geradora_especifica = opcoes_documentos_dict[tipo_selecionado_nome]
            
            # Lógica para buscar/mostrar documento existente e gerar novo
            documento_existente_conteudo = None
            try:
                doc_ref = db.collection('projetos').document(projeto_id)
                doc_snapshot = doc_ref.get()
                if doc_snapshot.exists:
                    projeto_data = doc_snapshot.to_dict()
                    documentos_salvos = projeto_data.get('documentos', {})
                    if isinstance(documentos_salvos, dict):
                        documento_existente_conteudo = documentos_salvos.get(chave_doc_selecionado)
            except Exception as e:
                st.error(f"Erro ao buscar '{tipo_selecionado_nome}' existente: {str(e)}")

            # Chave para gerenciar o estado do documento na sessão
            chave_sessao_doc_atual = f"doc_gerado_{chave_doc_selecionado}_{projeto_id}"

            # Botão para (Re)Gerar o documento
            if st.button(f"🔄 Gerar Nova Versão de '{tipo_selecionado_nome}'" if documento_existente_conteudo else f"✨ Gerar '{tipo_selecionado_nome}'", 
                         key=f"btn_gerar_{chave_doc_selecionado}_{projeto_id}"):
                with st.spinner(f"Gerando '{tipo_selecionado_nome}'..."):
                    try:
                        # Criar um container vazio para o streaming
                        doc_container = st.empty()
                        doc_texto_stream = ""
                        
                        def update_doc_stream(text):
                            nonlocal doc_texto_stream
                            doc_texto_stream += text
                            doc_container.markdown(doc_texto_stream)
                            time.sleep(0.005)  # Pequeno delay para visualização suave

                        if funcao_geradora_especifica:
                            # Para funções específicas, precisamos adaptar para streaming
                            response = funcao_geradora_especifica(texto_base_projeto, context=diagnostico_base_projeto, llm=llm)
                            for char in response:
                                update_doc_stream(char)
                            novo_documento_gerado = doc_texto_stream
                        else:
                            prompt_geracao_doc_generico = f"""
Você é um especialista em elaboração de propostas para editais.
Com base no TEXTO DO PROJETO e, opcionalmente, no DIAGNÓSTICO fornecido, sua tarefa é gerar um documento detalhado e completo do tipo: '{tipo_selecionado_nome}'.
Este documento deve ser bem estruturado, coerente com o projeto e atender às expectativas para um documento deste tipo em um contexto de edital.
Se o diagnóstico contiver informações pertinentes para este tipo de documento, incorpore-as de forma inteligente.

TEXTO DO PROJETO:
{texto_base_projeto}

DIAGNÓSTICO DO PROJETO (use com discernimento, pode não ser totalmente relevante para este documento específico):
{diagnostico_base_projeto if diagnostico_base_projeto else "Nenhum diagnóstico fornecido."}

Por favor, gere o documento '{tipo_selecionado_nome}':
"""
                            # Usar streaming para a resposta do LLM
                            for chunk in llm.stream(prompt_geracao_doc_generico):
                                if hasattr(chunk, 'content'):
                                    update_doc_stream(chunk.content)
                                else:
                                    update_doc_stream(str(chunk))
                            novo_documento_gerado = doc_texto_stream.strip()
                        
                        st.session_state[chave_sessao_doc_atual] = novo_documento_gerado
                        st.success(f"'{tipo_selecionado_nome}' gerado/atualizado! Revise abaixo e salve.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao gerar '{tipo_selecionado_nome}': {str(e)}")
                        st.code(traceback.format_exc())
            
            # Mostrar área de edição/visualização para documento
            conteudo_para_mostrar = ""
            subtitulo_area = ""

            if chave_sessao_doc_atual in st.session_state:
                conteudo_para_mostrar = st.session_state[chave_sessao_doc_atual]
                subtitulo_area = f"📝 Edição de '{tipo_selecionado_nome}'"
            elif documento_existente_conteudo:
                conteudo_para_mostrar = documento_existente_conteudo
                subtitulo_area = f"📄 '{tipo_selecionado_nome}'"
                st.session_state[chave_sessao_doc_atual] = documento_existente_conteudo
            
            if subtitulo_area:
                st.subheader(subtitulo_area)
                doc_editado_na_sessao = st.text_area(
                    "Conteúdo do documento:",
                    value=conteudo_para_mostrar,
                    height=350,
                    key=f"textarea_{chave_doc_selecionado}_{projeto_id}"
                )
                
                # Atualiza sessão se editado
                if doc_editado_na_sessao != st.session_state.get(chave_sessao_doc_atual):
                    st.session_state[chave_sessao_doc_atual] = doc_editado_na_sessao

                # Botão Salvar e Download
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"💾 Salvar '{tipo_selecionado_nome}'", key=f"btn_salvar_{chave_doc_selecionado}_{projeto_id}"):
                        try:
                            doc_ref_save = db.collection('projetos').document(projeto_id)
                            doc_snapshot_save = doc_ref_save.get()
                            current_project_data = doc_snapshot_save.to_dict() if doc_snapshot_save.exists else {}
                            
                            documentos_map = current_project_data.get('documentos', {})
                            if not isinstance(documentos_map, dict):
                                documentos_map = {}
                            
                            documentos_map[chave_doc_selecionado] = st.session_state[chave_sessao_doc_atual]
                            
                            doc_ref_save.set({
                                'documentos': documentos_map,
                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                            }, merge=True)
                            
                            st.success(f"'{tipo_selecionado_nome}' salvo com sucesso!")
                            del st.session_state[chave_sessao_doc_atual]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao salvar '{tipo_selecionado_nome}': {str(e)}")
                            st.code(traceback.format_exc())
                
                with col2:
                    if documento_existente_conteudo:
                        st.download_button(
                            label=f"⏬ Baixar '{tipo_selecionado_nome}'",
                            data=documento_existente_conteudo,
                            file_name=f"{slugify(projeto.get('nome','projeto'))}_{chave_doc_selecionado}.txt",
                            mime="text/plain",
                            key=f"dl_{chave_doc_selecionado}_{projeto_id}"
                        )
            elif not lista_documentos_sugeridos and not usando_lista_padrao and edital_associado_id:
                st.info("Clique em 'Analisar Edital para Sugerir Documentos' para começar.")
            elif not opcoes_documentos_dict:
                st.warning(f"Nenhum documento '{tipo_selecionado_nome}' encontrado ou gerado para este projeto.")