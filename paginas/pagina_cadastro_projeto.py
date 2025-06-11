import streamlit as st
import firebase_admin
from firebase_admin import firestore
import traceback
from datetime import datetime
import time

def pagina_cadastro_projeto():
    st.title("✨ Criar Novo Projeto")

    if not firebase_admin._apps:
        pass
    db = firestore.client()

    # Busca editais disponíveis
    try:
        editais_ref = db.collection('editais').order_by('nome')
        editais = editais_ref.get()
        editais_lista = [{'id': doc.id, **doc.to_dict()} for doc in editais]
    except Exception as e:
        st.error(f"Erro ao carregar editais: {str(e)}")
        editais_lista = []

    with st.form("form_cadastro_projeto"):
        # Campos básicos
        nome = st.text_input("Nome do Projeto*", help="Nome principal do projeto")
        descricao = st.text_area("Descrição do Projeto*", height=150, help="Descreva os objetivos e características principais do projeto")
        
        # Categorias padrão
        categorias = [
            "Artes Visuais", "Música", "Teatro", "Dança", 
            "Cinema e Audiovisual", "Literatura", "Patrimônio Cultural",
            "Artesanato", "Cultura Popular", "Outra"
        ]
        categoria = st.selectbox("Categoria*", categorias, help="Selecione a categoria principal do projeto")
        
        # Seleção de edital (opcional)
        edital_options = {'-- Selecione um Edital (Opcional) --': None}
        edital_options.update({edital['nome']: edital['id'] for edital in editais_lista})
        edital_selecionado = st.selectbox(
            "Associar a um Edital",
            list(edital_options.keys()),
            help="Selecione um edital para associar este projeto (opcional)"
        )

        # Botões de ação
        col1, col2 = st.columns([1, 1])
        with col1:
            submit = st.form_submit_button("💾 Salvar Projeto")
        with col2:
            if st.form_submit_button("↩️ Voltar"):
                st.session_state['pagina_atual'] = 'projetos'
                st.rerun()

        if submit:
            if not nome or not descricao or not categoria:
                st.error("Por favor, preencha todos os campos obrigatórios (*).")
            else:
                try:
                    # Prepara dados do projeto
                    projeto_data = {
                        'nome': nome,
                        'descricao': descricao,
                        'categoria': categoria,
                        'edital_associado': edital_options[edital_selecionado],
                        'user_id': st.session_state.get('user', {}).get('uid'),
                        'data_criacao': firestore.SERVER_TIMESTAMP,
                        'ultima_atualizacao': firestore.SERVER_TIMESTAMP
                    }

                    # Salva no Firestore
                    doc_ref = db.collection('projetos').add(projeto_data)
                    st.success(f"Projeto '{nome}' criado com sucesso!")
                    time.sleep(1)
                    st.session_state['pagina_atual'] = 'projetos'
                    st.rerun()

                except Exception as e:
                    st.error(f"Erro ao salvar projeto: {str(e)}")
                    st.code(traceback.format_exc())

    # Botão Voltar fora do form
    if st.button("⬅️ Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun() 