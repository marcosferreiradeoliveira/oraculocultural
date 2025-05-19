import streamlit as st
import firebase_admin
from firebase_admin import firestore
import tempfile
import os
import traceback

from loaders import carrega_pdf

def pagina_cadastro_edital():
    st.title("📥 Cadastro de Novo Edital")

    # Inicializa o Firestore (se já não estiver inicializado em app.py)
    # Esta verificação evita a reinicialização em reruns
    if not firebase_admin._apps:
        # Assume que a inicialização com credenciais já ocorreu em app.py
        # Pode ser necessário ajustar se a lógica de inicialização for diferente
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
                    'user_id': st.session_state.get('user', {}).get('uid'), # Opcional: associar ao usuário
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
                    db.collection('editais').add(edital_data)
                    st.success(f"Edital '{nome_edital}' cadastrado com sucesso!")

                    # Opcional: Limpar formulário ou redirecionar
                    # st.session_state['pagina_atual'] = 'projetos'
                    # st.rerun()

                except Exception as e:
                    st.error(f"Erro ao cadastrar edital: {str(e)}")
                    st.text("Detalhes do erro:")
                    st.code(traceback.format_exc())

    if st.button("⬅️ Voltar para Projetos"):
        st.session_state['pagina_atual'] = 'projetos'
        st.rerun() 