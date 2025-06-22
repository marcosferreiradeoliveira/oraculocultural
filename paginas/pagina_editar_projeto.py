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
import random
from constants import USER_SESSION_KEY, AUTENTICADO_SESSION_KEY, PAGINA_ATUAL_SESSION_KEY
from utils.analytics import track_event, track_page_view

llm = get_llm() # LLM global instanciada

def slugify(text):
    if not text: return ""
    text = text.replace(' ', '_')
    text = re.sub(r'[^\w_]', '', text) # Remove non-alphanumeric (except underscore)
    return text.lower()

def retry_with_backoff(func, max_retries=3, initial_delay=1):
    """Função para tentar novamente com backoff exponencial"""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "insufficient_quota" not in str(e).lower() or attempt == max_retries - 1:
                raise e
            
            delay = initial_delay * (2 ** attempt) + random.uniform(0, 1)
            st.warning(f"⚠️ Tentativa {attempt + 1} falhou. Aguardando {delay:.1f} segundos antes de tentar novamente...")
            time.sleep(delay)
            st.rerun()

def pagina_editar_projeto():
    """Página de edição com menu lateral de 3 seções"""
    
    # Track page view
    track_page_view('Edit Project Page')
    
    # Initialize secao_atual if not present
    if 'secao_atual' not in st.session_state:
        st.session_state['secao_atual'] = "📥 Carregar Projeto"
    
    st.markdown("""
    <style>
        /* Sidebar padrão para desktop */
        section[data-testid="stSidebar"] {
            min-width: 250px !important;
            width: 250px !important;
            visibility: visible !important;
            transform: none !important;
            transition: all 0.3s ease;
        }
        section[data-testid="stSidebar"] > div {padding-top: 2rem;}
        section[data-testid="stSidebar"] > div > div {padding-top: 2rem;}
        div[data-testid="collapsedControl"] {display: none !important;}

        /* Responsividade: recolher sidebar em telas pequenas */
        @media (max-width: 992px) {
            section[data-testid="stSidebar"] {
                min-width: 0 !important;
                width: 0 !important;
                visibility: hidden !important;
                transform: translateX(-100%) !important;
                padding: 0 !important;
            }
            /* Mostra o botão de expandir sidebar do Streamlit */
            div[data-testid="collapsedControl"] {display: block !important;}
            .stApp main, .stApp .block-container {
                padding: 0.5rem !important;
            }
            .stApp h1, .stApp h2, .stApp h3 {
                font-size: 1.1rem !important;
                margin-bottom: 0.5rem !important;
            }
            .stApp .stTextInput input, .stApp .stTextArea textarea {
                font-size: 1rem !important;
            }
            .stApp .stButton button {
                font-size: 1rem !important;
                padding: 0.5rem 1rem !important;
            }
            .stApp .project-card {
                min-height: 120px !important;
                padding: 0.5rem !important;
            }
            .stApp .project-card h3 {
                font-size: 1rem !important;
            }
            .stApp .project-description {
                -webkit-line-clamp: 6 !important;
                max-height: 8em !important;
            }
        }
        @media (max-width: 600px) {
            .stApp main, .stApp .block-container {
                padding: 0.1rem !important;
            }
            .stApp h1, .stApp h2, .stApp h3 {
                font-size: 1rem !important;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    try:
        if not firebase_admin._apps:
            if not initialize_firebase():
                st.sidebar.error(get_error_message())
                return
        db = firestore.client()
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

    # Menu lateral
    st.sidebar.title("Menu")
    if st.sidebar.button("Projeto", key="nav_carregar", use_container_width=True, disabled=st.session_state['secao_atual'] == "📥 Carregar Projeto"):
        st.session_state['secao_atual'] = "📥 Carregar Projeto"
        st.rerun()
    
    if st.sidebar.button("Diagnóstico", key="nav_diagnostico", use_container_width=True, disabled=st.session_state['secao_atual'] == "🔍 Fazer Diagnóstico"):
        st.session_state['secao_atual'] = "🔍 Fazer Diagnóstico"
        st.rerun()
    
    if st.sidebar.button("Documentos", key="nav_documentos", use_container_width=True, disabled=st.session_state['secao_atual'] == "📄 Gerar Documentos"):
        st.session_state['secao_atual'] = "📄 Gerar Documentos"
        st.rerun()

    # Botão Voltar
    st.sidebar.divider()
    if st.sidebar.button("⬅️ Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        # Limpar estados específicos da página de edição ao sair
        keys_to_clear = [k for k in st.session_state.keys() if projeto_id in k or 'diagnostico_editavel' in k or 'doc_gerado' in k]
        for key in keys_to_clear:
            del st.session_state[key]
        st.rerun()

    # Título da seção atual
    if st.session_state['secao_atual'] == "📥 Carregar Projeto":
        st.title("Projeto")
    elif st.session_state['secao_atual'] == "🔍 Fazer Diagnóstico":
        st.title("Diagnóstico")
    elif st.session_state['secao_atual'] == "📄 Gerar Documentos":
        st.title("Documentos")

    # --- Seção 1: Carregar Projeto ---
    if st.session_state['secao_atual'] == "📥 Carregar Projeto":
        if 'ultimas_alteracoes' in st.session_state and st.session_state['ultimas_alteracoes']['projeto_id'] == projeto_id:
            st.success("✅ Alterações aplicadas com sucesso!")
            st.write(st.session_state['ultimas_alteracoes']['alteracoes'])
            del st.session_state['ultimas_alteracoes']

        texto_inicial_textarea = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', ''))

        # Initialize current_texto_input for the specific project if not set or project changed
        if st.session_state.get(f'current_texto_input_pid') != projeto_id:
            st.session_state[f'current_texto_input_{projeto_id}'] = texto_inicial_textarea
            st.session_state[f'current_texto_input_pid'] = projeto_id

        modo_entrada = st.radio("Escolha a forma de entrada:", ["✍️ Digitar texto", "📄 Importar PDF"], horizontal=True, key=f"modo_entrada_{projeto_id}")

        if modo_entrada == "✍️ Digitar texto":
            texto_digitado = st.text_area("Conteúdo do projeto", 
                                       value=st.session_state.get(f'current_texto_input_{projeto_id}', texto_inicial_textarea), 
                                       height=300, 
                                       key=f"caixa_texto_manual_{projeto_id}")
            if texto_digitado != st.session_state.get(f'current_texto_input_{projeto_id}'):
                st.session_state[f'current_texto_input_{projeto_id}'] = texto_digitado

        elif modo_entrada == "📄 Importar PDF":
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
                                st.text_area("Visualização do conteúdo extraído", 
                                        value=st.session_state[f'current_texto_input_{projeto_id}'], 
                                        height=200, 
                                        key=f"visualizacao_pdf_{projeto_id}", 
                                        disabled=True)
                        except Exception as e:
                            st.error(f"Erro ao extrair texto do PDF: {str(e)}")
                            if "password" in str(e).lower():
                                st.error("O PDF parece estar protegido por senha. Por favor, remova a proteção e tente novamente.")
                            elif "400" in str(e):
                                st.error("Erro ao processar o PDF. O arquivo pode estar corrompido ou em formato não suportado.")
                            st.code(traceback.format_exc())
                        finally:
                            try:
                                os.remove(temp_path)
                            except:
                                pass
                    except Exception as e:
                        st.error(f"Erro ao processar PDF: {str(e)}")
                        st.code(traceback.format_exc())
        
        texto_para_salvar = st.session_state.get(f'current_texto_input_{projeto_id}', '')

        if st.button("💾 Salvar", key=f"salvar_conteudo_{projeto_id}"):
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
                            st.session_state[f'texto_projeto_{projeto_id}'] = texto_para_salvar.strip()
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

        # Campo de prompt para alterar o texto
        st.divider()
        st.subheader("🤖 Alterar texto com IA")
        prompt_alteracao = st.text_area("Digite suas instruções para alterar o texto:", height=100, key=f"prompt_alteracao_{projeto_id}")
        
        if st.button("✨ Aplicar Alterações", key=f"aplicar_alteracoes_{projeto_id}"):
            if prompt_alteracao.strip():
                with st.spinner("Processando alterações..."):
                    try:
                        texto_atual = st.session_state.get(f'current_texto_input_{projeto_id}', '')
                        prompt_template = f"""
Você é um editor especialista em aprimorar textos de projetos.
Com base nas instruções fornecidas, modifique o texto do projeto mantendo sua essência e estrutura.

[INSTRUÇÕES DE ALTERAÇÃO]:
{prompt_alteracao}

[TEXTO ORIGINAL DO PROJETO]:
{texto_atual}

Por favor, forneça o texto modificado seguindo as instruções acima. Mantenha a estrutura geral do texto, apenas aplicando as alterações solicitadas.
"""
                        # Criar um container vazio para o streaming
                        texto_container = st.empty()
                        texto_modificado_stream = ""
                        update_counter = 0
                        
                        def update_texto_stream(text):
                            nonlocal texto_modificado_stream, update_counter
                            texto_modificado_stream += text
                            update_counter += 1
                            texto_container.text_area("Conteúdo do projeto", 
                                                   value=texto_modificado_stream,
                                                   height=300,
                                                   key=f"texto_modificado_stream_{projeto_id}_{update_counter}")
                            time.sleep(0.005)  # Pequeno delay para visualização suave

                        # Usar streaming para a resposta do LLM
                        for chunk in llm.stream(prompt_template):
                            if hasattr(chunk, 'content'):
                                update_texto_stream(chunk.content)
                            else:
                                update_texto_stream(str(chunk))
                        
                        texto_modificado = texto_modificado_stream.strip()
                        
                        if texto_modificado:
                            # Atualizar o estado da sessão com o texto final
                            st.session_state[f'current_texto_input_{projeto_id}'] = texto_modificado
                            st.success("✅ Alterações aplicadas! Revise o texto acima e salve se estiver satisfeito.")
                            st.rerun()  # Rerun apenas uma vez no final
                        else:
                            st.error("Não foi possível gerar alterações no texto.")
                    except Exception as e:
                        st.error(f"Erro ao processar alterações: {str(e)}")
                        st.code(traceback.format_exc())
            else:
                st.warning("Por favor, forneça instruções para as alterações.")

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
                        update_counter = 0
                        buffer = ""
                        
                        def update_diagnostico_stream(text):
                            nonlocal diagnostico_texto_stream, update_counter, buffer
                            buffer += text
                            # Atualiza a cada 50 caracteres ou quando receber uma quebra de linha
                            if len(buffer) >= 50 or '\n' in text:
                                diagnostico_texto_stream += buffer
                                update_counter += 1
                                diagnostico_container.text_area("Diagnóstico", 
                                                             value=diagnostico_texto_stream,
                                                             height=400,
                                                             key=f"diagnostico_stream_{projeto_id}_{update_counter}")
                                buffer = ""
                        
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
                        
                        # Garantir que o buffer final seja processado
                        if buffer:
                            update_diagnostico_stream("\n")
                        
                        update_diagnostico_stream("\n\n")
                        
                        comparativo_stream = comparar_com_selecionados(texto_projeto_atual, texto_edital_context, texto_selecionados_context)
                        for char in comparativo_stream: 
                            update_diagnostico_stream(char)
                        
                        # Garantir que o buffer final seja processado
                        if buffer:
                            update_diagnostico_stream("\n")
                        
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
                st.subheader("🤖 Ver Sugestões de Melhorias no Texto do Projeto")
                st.markdown("""
                A IA analisará o diagnóstico e sugerirá melhorias específicas para o texto do projeto.
                Você poderá revisar e aprovar cada sugestão individualmente antes de aplicá-las.
                """)

                diagnostico_para_aplicar = st.session_state.get(f'diagnostico_editavel_{projeto_id}', texto_diagnostico_atual_db)

                if st.button("✨ Ver Sugestões de Melhorias", key=f"ver_sugestoes_{projeto_id}"):
                    if not diagnostico_para_aplicar.strip():
                        st.warning("O diagnóstico está vazio. Não é possível gerar sugestões.")
                    else:
                        with st.spinner("IA analisando e preparando sugestões de melhorias..."):
                            try:
                                # Buscar o texto atual do projeto da sessão
                                texto_projeto_atual = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', ''))
                                
                                if not texto_projeto_atual.strip():
                                    st.warning("O texto do projeto está vazio. Por favor, adicione conteúdo na seção 'Carregar Projeto' primeiro.")
                                    return

                                prompt_template_sugestoes = """
Você é um editor especialista em aprimorar propostas de projetos e editais.
Analise o TEXTO ORIGINAL DO PROJETO e o DIAGNÓSTICO DO PROJETO fornecidos.

O DIAGNÓSTICO contém uma análise detalhada dos pontos fortes e fracos do projeto, bem como recomendações de melhoria.
Sua tarefa é usar essas informações do diagnóstico para identificar trechos específicos no TEXTO ORIGINAL DO PROJETO que precisam ser melhorados.

Para cada problema identificado no diagnóstico:
1. Encontre o trecho correspondente no texto original do projeto que precisa ser modificado
2. Baseado nas recomendações do diagnóstico, proponha uma melhoria específica para esse trecho
3. Forneça o novo texto que deve substituir o trecho original

Formate cada sugestão assim:
[SUGESTÃO X]
Trecho Original: [copie o trecho exato do texto original do projeto que precisa ser melhorado]
Proposta de Mudança: [explique como este trecho deve ser melhorado, baseado no diagnóstico]
Novo Texto: [forneça o novo texto que deve substituir o trecho original]

[TEXTO ORIGINAL DO PROJETO]:
{texto_original}

[DIAGNÓSTICO DO PROJETO]:
{texto_diagnostico}

[SUGESTÕES DE MELHORIAS]:
"""
                                prompt_sugestoes = prompt_template_sugestoes.format(
                                    texto_original=texto_projeto_atual,
                                    texto_diagnostico=diagnostico_para_aplicar
                                )
                                try:
                                    def invoke_llm():
                                        response = llm.invoke(prompt_sugestoes)
                                        return response.content if hasattr(response, 'content') else str(response)
                                    
                                    sugestoes_texto = retry_with_backoff(invoke_llm).strip()
                                except Exception as e:
                                    error_msg = str(e)
                                    if "insufficient_quota" in error_msg.lower():
                                        st.error("""
                                        ⚠️ Erro de quota na API da OpenAI após várias tentativas. Isso pode ocorrer por:
                                        1. Limite de requisições por minuto atingido
                                        2. Problemas com a faturação da conta
                                        3. Saldo em uma conta diferente da configurada
                                        
                                        Por favor, verifique:
                                        - Se a conta está corretamente configurada
                                        - Se há saldo disponível na conta correta
                                        - Se a faturação está em dia
                                        - Aguarde alguns minutos e tente novamente
                                        """)
                                        
                                        # Adiciona botão para tentar novamente
                                        if st.button("🔄 Tentar Novamente"):
                                            st.rerun()
                                    else:
                                        st.error(f"Erro ao gerar sugestões: {error_msg}")
                                    st.code(traceback.format_exc())
                                    return

                                if not sugestoes_texto:
                                    st.error("A IA não retornou sugestões de melhorias.")
                                    return

                                # Processar e exibir as sugestões
                                sugestoes = []
                                sugestao_atual = {}
                                for linha in sugestoes_texto.split('\n'):
                                    if linha.startswith('[SUGESTÃO'):
                                        if sugestao_atual:
                                            sugestoes.append(sugestao_atual)
                                        sugestao_atual = {'numero': linha.strip('[]')}
                                    elif linha.startswith('Trecho Original:'):
                                        sugestao_atual['original'] = linha.replace('Trecho Original:', '').strip()
                                    elif linha.startswith('Proposta de Mudança:'):
                                        sugestao_atual['mudanca'] = linha.replace('Proposta de Mudança:', '').strip()
                                    elif linha.startswith('Novo Texto:'):
                                        sugestao_atual['novo'] = linha.replace('Novo Texto:', '').strip()
                                if sugestao_atual:
                                    sugestoes.append(sugestao_atual)

                                # Salvar sugestões no Firestore
                                try:
                                    doc_ref = db.collection('projetos').document(projeto_id)
                                    doc_ref.update({
                                        'sugestoes': sugestoes,
                                        'sugestoes_aprovadas': [],
                                        'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                                    })
                                except Exception as e:
                                    st.error(f"Erro ao salvar sugestões: {str(e)}")
                                    st.code(traceback.format_exc())

                                # Armazenar sugestões na sessão
                                st.session_state[f'sugestoes_{projeto_id}'] = sugestoes
                                st.session_state[f'sugestoes_aprovadas_{projeto_id}'] = []

                                st.success(f"✅ {len(sugestoes)} sugestões de melhorias identificadas!")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Erro ao gerar sugestões: {str(e)}")
                                st.code(traceback.format_exc())

                # Exibir sugestões para aprovação
                if f'sugestoes_{projeto_id}' in st.session_state:
                    sugestoes = st.session_state[f'sugestoes_{projeto_id}']
                    sugestoes_aprovadas = st.session_state.get(f'sugestoes_aprovadas_{projeto_id}', [])

                    # Carregar sugestões aprovadas do Firestore se não estiverem na sessão
                    if not sugestoes_aprovadas:
                        try:
                            doc_ref = db.collection('projetos').document(projeto_id)
                            doc_snapshot = doc_ref.get()
                            if doc_snapshot.exists:
                                projeto_data = doc_snapshot.to_dict()
                                sugestoes_aprovadas_db = projeto_data.get('sugestoes_aprovadas', [])
                                if sugestoes_aprovadas_db:
                                    sugestoes_aprovadas = sugestoes_aprovadas_db
                                    st.session_state[f'sugestoes_aprovadas_{projeto_id}'] = sugestoes_aprovadas
                        except Exception as e:
                            st.error(f"Erro ao carregar sugestões aprovadas: {str(e)}")

                    st.markdown("""
                    <style>
                        .sugestao-box {
                            background-color: #f8f9fa;
                            border-radius: 10px;
                            padding: 1rem;
                            margin-bottom: 1rem;
                            white-space: pre-wrap;
                            word-wrap: break-word;
                            max-width: 100%;
                            overflow-wrap: break-word;
                        }
                        .sugestao-box h4 {
                            margin-top: 0;
                            color: #2c3e50;
                            font-size: 1.1em;
                        }
                        .sugestao-box p {
                            margin: 0.5rem 0;
                            line-height: 1.5;
                            white-space: pre-wrap;
                            word-wrap: break-word;
                        }
                    </style>
                    """, unsafe_allow_html=True)

                    st.subheader("📝 Sugestões de Melhorias")
                    for i, sugestao in enumerate(sugestoes):
                        with st.expander(f"Sugestão {i+1}: {sugestao['mudanca'][:50]}..."):
                            st.markdown("**Trecho Original:**")
                            st.markdown(f'<div class="sugestao-box"><p>{sugestao["original"]}</p></div>', unsafe_allow_html=True)
                            
                            st.markdown("**Proposta de Mudança:**")
                            st.markdown(f'<div class="sugestao-box"><p>{sugestao["mudanca"]}</p></div>', unsafe_allow_html=True)
                            
                            st.markdown("**Novo Texto:**")
                            st.markdown(f'<div class="sugestao-box"><p>{sugestao["novo"]}</p></div>', unsafe_allow_html=True)
                            
                            if i not in sugestoes_aprovadas:
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(f"✅ Aprovar Sugestão {i+1}", key=f"aprovar_{i}_{projeto_id}"):
                                        sugestoes_aprovadas.append(i)
                                        st.session_state[f'sugestoes_aprovadas_{projeto_id}'] = sugestoes_aprovadas
                                        
                                        # Aplicar a sugestão ao texto do projeto
                                        texto_atual = st.session_state.get(f'texto_projeto_{projeto_id}', projeto.get('texto_projeto', ''))
                                        texto_original = sugestao['original']
                                        texto_novo = sugestao['novo']
                                        
                                        if texto_original in texto_atual:
                                            texto_atualizado = texto_atual.replace(texto_original, texto_novo)
                                            
                                            # Atualizar na sessão
                                            st.session_state[f'texto_projeto_{projeto_id}'] = texto_atualizado
                                            st.session_state[f'current_texto_input_{projeto_id}'] = texto_atualizado
                                            
                                            # Atualizar no Firestore
                                            try:
                                                doc_ref = db.collection('projetos').document(projeto_id)
                                                doc_ref.update({
                                                    'texto_projeto': texto_atualizado,
                                                    'sugestoes_aprovadas': sugestoes_aprovadas,
                                                    'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                                                })
                                                
                                                # Atualizar o projeto na sessão se existir
                                                if 'projeto_selecionado' in st.session_state and st.session_state['projeto_selecionado']['id'] == projeto_id:
                                                    st.session_state['projeto_selecionado']['texto_projeto'] = texto_atualizado
                                                
                                                # Forçar atualização da seção "Carregar Projeto"
                                                st.session_state['secao_atual'] = "📥 Carregar Projeto"
                                                st.success(f"Sugestão {i+1} aprovada e aplicada ao texto do projeto!")
                                                time.sleep(1)
                                                st.rerun()
                                            except Exception as e:
                                                st.error(f"Erro ao salvar alterações: {str(e)}")
                                        else:
                                            st.warning(f"Não foi possível encontrar o trecho original no texto do projeto.")
                                        
                                        st.rerun()
                                with col2:
                                    if st.button(f"❌ Recusar Sugestão {i+1}", key=f"recusar_{i}_{projeto_id}"):
                                        # Remover a sugestão da lista
                                        sugestoes.pop(i)
                                        st.session_state[f'sugestoes_{projeto_id}'] = sugestoes
                                        
                                        # Atualizar no Firestore
                                        try:
                                            doc_ref = db.collection('projetos').document(projeto_id)
                                            doc_ref.update({
                                                'sugestoes': sugestoes,
                                                'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                                            })
                                            st.success(f"Sugestão {i+1} removida!")
                                        except Exception as e:
                                            st.error(f"Erro ao remover sugestão: {str(e)}")
                                        
                                        st.rerun()
                            else:
                                st.button("✅ Sugestão Aprovada", key=f"aprovado_{i}_{projeto_id}", disabled=True)
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
                    track_event('generate_document_click')
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
                track_event('generate_document_click')
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