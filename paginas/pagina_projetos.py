import streamlit as st
import firebase_admin
from firebase_admin import firestore
import traceback
import time

def pagina_projetos():
    st.title("📋 Projetos")

    if not firebase_admin._apps:
        pass
    db = firestore.client()

    # Tabs para Projetos e Editais
    tab1, tab2 = st.tabs(["📝 Projetos", "📄 Editais"])

    with tab1:
        # Código existente para listar projetos
        pass

    with tab2:
        st.subheader("Editais Disponíveis")
        
        # Botão para adicionar novo edital
        if st.button("📥 Adicionar Novo Edital", use_container_width=True):
            st.session_state['pagina_atual'] = 'cadastro_edital'
            st.rerun()
        
        st.markdown("---")
        
        # Busca editais no Firestore
        try:
            editais_ref = db.collection('editais').order_by('data_upload', direction=firestore.Query.DESCENDING)
            editais = editais_ref.get()
            
            if not editais:
                st.info("Nenhum edital cadastrado ainda.")
            else:
                for edital in editais:
                    edital_data = edital.to_dict()
                    with st.expander(f"📄 {edital_data.get('nome', 'Edital sem nome')}", expanded=True):
                        # Informações do edital
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
                        
                        # Botões de ação em uma linha separada
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✏️ Editar Edital", key=f"edit_{edital.id}", use_container_width=True):
                                st.session_state['edital_para_editar'] = edital.id
                                st.session_state['pagina_atual'] = 'editar_edital'
                                st.rerun()
                        
                        with col2:
                            if st.button("🗑️ Excluir Edital", key=f"delete_{edital.id}", use_container_width=True):
                                # Verifica se existem projetos associados
                                projetos_ref = db.collection('projetos').where('edital_associado', '==', edital.id).get()
                                if len(projetos_ref) > 0:
                                    st.error("Não é possível excluir este edital pois existem projetos associados a ele.")
                                else:
                                    if st.checkbox("Confirmar exclusão", key=f"confirm_delete_{edital.id}"):
                                        try:
                                            db.collection('editais').document(edital.id).delete()
                                            st.success("Edital excluído com sucesso!")
                                            time.sleep(1)
                                            st.rerun()
                                        except Exception as e:
                                            st.error(f"Erro ao excluir edital: {str(e)}")
                                            st.code(traceback.format_exc())
        
        except Exception as e:
            st.error(f"Erro ao carregar editais: {str(e)}")
            st.code(traceback.format_exc())

    # Botão para adicionar novo projeto
    if st.button("📝 Novo Projeto", use_container_width=True):
        st.session_state['pagina_atual'] = 'cadastro_projeto'
        st.rerun() 