import streamlit as st
import firebase_admin
from firebase_admin import firestore
import tempfile
import os
import traceback
from models import get_llm

from loaders import carrega_pdf

def extrair_info_edital(texto_edital):
    """Extrai informações importantes do edital usando IA"""
    llm = get_llm()
    
    prompt = f"""
Analise o texto do edital abaixo e extraia as seguintes informações em formato estruturado:

1. Data de inscrição (ou período de inscrição)
2. Categorias de projetos aceitas
3. Textos que precisam ser enviados (como objetivo, justificativa, etc)
4. Documentos que devem ser enviados (como anexos, declarações, etc)

Formate a resposta assim:
[DATA_INSCRICAO]
[data ou período de inscrição]

[CATEGORIAS]
- categoria 1
- categoria 2
...

[TEXTOS_REQUERIDOS]
- texto 1
- texto 2
...

[DOCUMENTOS_REQUERIDOS]
- documento 1
- documento 2
...

[TEXTO DO EDITAL]
{texto_edital}
"""
    try:
        response = llm.invoke(prompt)
        return response.content if hasattr(response, 'content') else str(response)
    except Exception as e:
        st.error(f"Erro ao extrair informações do edital: {str(e)}")
        return None

def pagina_editar_edital(edital_id):
    """Página para editar um edital existente"""
    st.title("✏️ Editar Edital")
    
    if not firebase_admin._apps:
        pass
    db = firestore.client()
    
    # Carrega dados do edital
    try:
        doc_ref = db.collection('editais').document(edital_id)
        doc = doc_ref.get()
        if not doc.exists:
            st.error("Edital não encontrado")
            return
        
        edital_data = doc.to_dict()
        
        with st.form("editar_edital_form"):
            nome_edital = st.text_input("Nome do Edital*", value=edital_data.get('nome', ''))
            arquivo_edital_pdf = st.file_uploader("Novo Arquivo do Edital (PDF)", type=["pdf"], 
                                                help="Carregue um novo PDF apenas se desejar substituir o atual.")
            arquivo_selecionados_pdf = st.file_uploader("Novo Estudo de Projetos Selecionados (PDF)", type=["pdf"],
                                                      help="Carregue um novo PDF apenas se desejar substituir o atual.")
            
            # Mostra informações atuais
            st.subheader("📅 Informações Atuais do Edital")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Data de Inscrição:**")
                st.write(edital_data.get('data_inscricao', 'Não definida'))
                
                st.write("**Categorias de Projetos:**")
                for cat in edital_data.get('categorias', []):
                    st.write(f"- {cat}")
            
            with col2:
                st.write("**Textos Requeridos:**")
                for texto in edital_data.get('textos_requeridos', []):
                    st.write(f"- {texto}")
                
                st.write("**Documentos Requeridos:**")
                for doc in edital_data.get('documentos_requeridos', []):
                    st.write(f"- {doc}")
            
            submitted = st.form_submit_button("💾 Salvar Alterações")
            
            if submitted:
                if not nome_edital:
                    st.error("Por favor, preencha o nome do edital.")
                else:
                    update_data = {
                        'nome': nome_edital,
                        'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                    }
                    
                    try:
                        # Processa novo PDF do edital se fornecido
                        if arquivo_edital_pdf:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                tmp_file.write(arquivo_edital_pdf.getvalue())
                                caminho_tmp_pdf = tmp_file.name
                            
                            texto_edital = carrega_pdf(caminho_tmp_pdf)
                            os.remove(caminho_tmp_pdf)
                            
                            if texto_edital:
                                update_data['texto_edital'] = texto_edital
                                
                                # Re-extrai informações do novo texto
                                with st.spinner("Analisando novo edital e extraindo informações..."):
                                    info_extraida = extrair_info_edital(texto_edital)
                                    if info_extraida:
                                        secoes = info_extraida.split('\n\n')
                                        for secao in secoes:
                                            if secao.startswith('[DATA_INSCRICAO]'):
                                                update_data['data_inscricao'] = secao.replace('[DATA_INSCRICAO]', '').strip()
                                            elif secao.startswith('[CATEGORIAS]'):
                                                categorias = secao.replace('[CATEGORIAS]', '').strip()
                                                update_data['categorias'] = [cat.strip('- ') for cat in categorias.split('\n') if cat.strip()]
                                            elif secao.startswith('[TEXTOS_REQUERIDOS]'):
                                                textos = secao.replace('[TEXTOS_REQUERIDOS]', '').strip()
                                                update_data['textos_requeridos'] = [texto.strip('- ') for texto in textos.split('\n') if texto.strip()]
                                            elif secao.startswith('[DOCUMENTOS_REQUERIDOS]'):
                                                docs = secao.replace('[DOCUMENTOS_REQUERIDOS]', '').strip()
                                                update_data['documentos_requeridos'] = [doc.strip('- ') for doc in docs.split('\n') if doc.strip()]
                            else:
                                st.warning("Não foi possível extrair texto do novo PDF do edital.")
                        
                        # Processa novo PDF de selecionados se fornecido
                        if arquivo_selecionados_pdf:
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                                tmp_file.write(arquivo_selecionados_pdf.getvalue())
                                caminho_tmp_pdf_selecionados = tmp_file.name
                            
                            texto_selecionados = carrega_pdf(caminho_tmp_pdf_selecionados)
                            os.remove(caminho_tmp_pdf_selecionados)
                            
                            if texto_selecionados:
                                update_data['texto_selecionados'] = texto_selecionados
                            else:
                                st.warning("Não foi possível extrair texto do novo PDF de projetos selecionados.")
                        
                        # Atualiza no Firestore
                        doc_ref.update(update_data)
                        st.success("Edital atualizado com sucesso!")
                        time.sleep(1)
                        st.session_state['pagina_atual'] = 'projetos'
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Erro ao atualizar edital: {str(e)}")
                        st.code(traceback.format_exc())
        
        # Botão para excluir edital
        if st.button("🗑️ Excluir Edital", type="primary"):
            if st.checkbox("Confirmar exclusão do edital"):
                try:
                    # Verifica se existem projetos associados
                    projetos_ref = db.collection('projetos').where('edital_associado', '==', edital_id).get()
                    if len(projetos_ref) > 0:
                        st.error("Não é possível excluir este edital pois existem projetos associados a ele.")
                    else:
                        doc_ref.delete()
                        st.success("Edital excluído com sucesso!")
                        time.sleep(1)
                        st.session_state['pagina_atual'] = 'projetos'
                        st.rerun()
                except Exception as e:
                    st.error(f"Erro ao excluir edital: {str(e)}")
                    st.code(traceback.format_exc())
        
        # Botão Voltar
        if st.button("⬅️ Voltar para Projetos"):
            st.session_state['pagina_atual'] = 'projetos'
            st.rerun()
            
    except Exception as e:
        st.error(f"Erro ao carregar edital: {str(e)}")
        st.code(traceback.format_exc())

def pagina_cadastro_edital():
    st.title("📥 Cadastro de Novo Edital")

    # Inicializa o Firestore (se já não estiver inicializado em app.py)
    if not firebase_admin._apps:
        pass
    db = firestore.client()

    with st.form("cadastro_edital_form"):
        nome_edital = st.text_input("Nome do Edital*", help="Nome de identificação do edital (ex: Edital Cultural Vale 2025)")
        arquivo_edital_pdf = st.file_uploader("Arquivo do Edital (PDF)*", type=["pdf"], help="Carregue o PDF oficial completo do edital.")
        arquivo_selecionados_pdf = st.file_uploader("Estudo de Projetos Selecionados (PDF)", type=["pdf"], help="Carregue um PDF com análises de projetos selecionados em editais anteriores (opcional)." )

        submitted = st.form_submit_button("💾 Salvar Edital")

        if submitted:
            if not nome_edital or not arquivo_edital_pdf:
                st.error("Por favor, preencha o nome do edital e carregue o arquivo PDF obrigatório.")
            else:
                edital_data = {
                    'nome': nome_edital,
                    'data_upload': firestore.SERVER_TIMESTAMP,
                    'user_id': st.session_state.get('user', {}).get('uid'),
                }

                try:
                    # Processa e salva o PDF do edital
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                        tmp_file.write(arquivo_edital_pdf.getvalue())
                        caminho_tmp_pdf = tmp_file.name

                    texto_edital = carrega_pdf(caminho_tmp_pdf)
                    os.remove(caminho_tmp_pdf)

                    if texto_edital:
                        edital_data['texto_edital'] = texto_edital
                        
                        # Extrai informações do edital
                        with st.spinner("Analisando edital e extraindo informações..."):
                            info_extraida = extrair_info_edital(texto_edital)
                            if info_extraida:
                                # Processa as informações extraídas
                                secoes = info_extraida.split('\n\n')
                                for secao in secoes:
                                    if secao.startswith('[DATA_INSCRICAO]'):
                                        edital_data['data_inscricao'] = secao.replace('[DATA_INSCRICAO]', '').strip()
                                    elif secao.startswith('[CATEGORIAS]'):
                                        categorias = secao.replace('[CATEGORIAS]', '').strip()
                                        edital_data['categorias'] = [cat.strip('- ') for cat in categorias.split('\n') if cat.strip()]
                                    elif secao.startswith('[TEXTOS_REQUERIDOS]'):
                                        textos = secao.replace('[TEXTOS_REQUERIDOS]', '').strip()
                                        edital_data['textos_requeridos'] = [texto.strip('- ') for texto in textos.split('\n') if texto.strip()]
                                    elif secao.startswith('[DOCUMENTOS_REQUERIDOS]'):
                                        docs = secao.replace('[DOCUMENTOS_REQUERIDOS]', '').strip()
                                        edital_data['documentos_requeridos'] = [doc.strip('- ') for doc in docs.split('\n') if doc.strip()]
                    else:
                        st.warning("Não foi possível extrair texto do PDF do edital.")

                    # Processa e salva o PDF de selecionados (se existir)
                    if arquivo_selecionados_pdf:
                         with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                            tmp_file.write(arquivo_selecionados_pdf.getvalue())
                            caminho_tmp_pdf_selecionados = tmp_file.name

                         texto_selecionados = carrega_pdf(caminho_tmp_pdf_selecionados)
                         os.remove(caminho_tmp_pdf_selecionados)

                         if texto_selecionados:
                            edital_data['texto_selecionados'] = texto_selecionados
                         else:
                            st.warning("Não foi possível extrair texto do PDF de projetos selecionados.")

                    # Salva os dados no Firestore
                    doc_ref = db.collection('editais').add(edital_data)
                    st.success(f"Edital '{nome_edital}' cadastrado com sucesso!")
                    
                    # Mostra as informações extraídas
                    if 'data_inscricao' in edital_data:
                        st.subheader("📅 Informações Extraídas do Edital")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write("**Data de Inscrição:**")
                            st.write(edital_data['data_inscricao'])
                            
                            st.write("**Categorias de Projetos:**")
                            for cat in edital_data.get('categorias', []):
                                st.write(f"- {cat}")
                        
                        with col2:
                            st.write("**Textos Requeridos:**")
                            for texto in edital_data.get('textos_requeridos', []):
                                st.write(f"- {texto}")
                            
                            st.write("**Documentos Requeridos:**")
                            for doc in edital_data.get('documentos_requeridos', []):
                                st.write(f"- {doc}")

                except Exception as e:
                    st.error(f"Erro ao cadastrar edital: {str(e)}")
                    st.text("Detalhes do erro:")
                    st.code(traceback.format_exc())

    if st.button("⬅️ Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun() 