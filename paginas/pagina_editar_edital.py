import streamlit as st
import firebase_admin
from firebase_admin import firestore
import traceback
from datetime import datetime
from loaders import carrega_pdf
from models import get_llm

def extrair_info_edital(texto_edital):
    """Extrai informações relevantes do texto do edital usando IA."""
    llm = get_llm()
    
    prompt = f"""Analise o seguinte texto de edital e extraia as seguintes informações em formato estruturado:

1. Data de inscrição (formato DD/MM/YYYY)
2. Categorias de projetos (lista de categorias disponíveis)
3. Textos que precisam ser enviados (objetivos, justificativas, etc.)
4. Documentos que devem ser enviados (anexos, declarações, etc.)

Texto do edital:
{texto_edital}

Retorne apenas um dicionário Python com as seguintes chaves:
- data_inscricao: string no formato DD/MM/YYYY
- categorias: lista de strings
- textos_requeridos: lista de strings
- documentos_requeridos: lista de strings

Se alguma informação não for encontrada, retorne uma lista vazia ou string vazia."""

    try:
        response = llm.invoke(prompt)
        return eval(response)  # Converte a string de resposta em dicionário Python
    except Exception as e:
        st.error(f"Erro ao extrair informações do edital: {str(e)}")
        return {
            'data_inscricao': '',
            'categorias': [],
            'textos_requeridos': [],
            'documentos_requeridos': []
        }

def pagina_editar_edital(edital_id):
    st.title("✏️ Editar Edital")

    if not firebase_admin._apps:
        pass
    db = firestore.client()

    try:
        # Carrega dados do edital
        edital_ref = db.collection('editais').document(edital_id)
        edital_doc = edital_ref.get()
        
        if not edital_doc.exists:
            st.error("Edital não encontrado")
            if st.button("Voltar para Projetos"):
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()
            return

        edital_data = edital_doc.to_dict()

        # Formulário de edição
        with st.form("form_editar_edital"):
            nome = st.text_input("Nome do Edital", value=edital_data.get('nome', ''))
            
            # Upload de novo PDF (opcional)
            novo_pdf = st.file_uploader("Novo PDF do Edital (opcional)", type=['pdf'])
            
            # Exibe informações atuais
            st.subheader("Informações Atuais")
            st.write("**Data de Inscrição:**")
            st.write(edital_data.get('data_inscricao', 'Não definida'))
            
            st.write("**Categorias de Projetos:**")
            for cat in edital_data.get('categorias', []):
                st.write(f"- {cat}")
            
            st.write("**Textos Requeridos:**")
            for texto in edital_data.get('textos_requeridos', []):
                st.write(f"- {texto}")
            
            st.write("**Documentos Requeridos:**")
            for doc in edital_data.get('documentos_requeridos', []):
                st.write(f"- {doc}")

            # Botões de ação
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                submit = st.form_submit_button("💾 Salvar Alterações")
            
            with col2:
                if st.form_submit_button("🗑️ Excluir Edital"):
                    # Verifica se existem projetos associados
                    projetos_ref = db.collection('projetos').where('edital_id', '==', edital_id).get()
                    if projetos_ref:
                        st.error("Não é possível excluir este edital pois existem projetos associados a ele.")
                    else:
                        edital_ref.delete()
                        st.success("Edital excluído com sucesso!")
                        st.session_state['pagina_atual'] = 'projetos'
                        st.rerun()
            
            with col3:
                if st.form_submit_button("↩️ Voltar"):
                    st.session_state['pagina_atual'] = 'projetos'
                    st.rerun()

            if submit:
                # Atualiza dados do edital
                edital_data['nome'] = nome
                edital_data['data_atualizacao'] = datetime.now()

                # Se um novo PDF foi enviado, processa-o
                if novo_pdf is not None:
                    with st.spinner("Processando novo PDF..."):
                        # Salva o PDF temporariamente
                        pdf_bytes = novo_pdf.read()
                        
                        # Extrai texto do PDF
                        texto_edital = carrega_pdf(pdf_bytes)
                        
                        # Extrai informações usando IA
                        info_edital = extrair_info_edital(texto_edital)
                        
                        # Atualiza dados com as novas informações
                        edital_data.update(info_edital)
                        
                        # Atualiza o PDF no Firestore
                        edital_data['pdf_url'] = f"editais/{edital_id}/{novo_pdf.name}"
                        # TODO: Implementar upload do PDF para o storage

                # Salva as alterações no Firestore
                edital_ref.update(edital_data)
                st.success("Edital atualizado com sucesso!")
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()

    except Exception as e:
        st.error(f"Erro ao editar edital: {str(e)}")
        st.code(traceback.format_exc()) 