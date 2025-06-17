import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
from datetime import datetime
import time
from constants import PAGINA_ATUAL_SESSION_KEY, USER_SESSION_KEY, AUTENTICADO_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message

def pagina_cadastro():
    """
    Página de Cadastro de Usuário
    """
    # Inicializa o Firebase (com cache)
    firebase_app = initialize_firebase_app()
    if not firebase_app:
        return

    st.title("📝 Cadastro")

    # Botão de voltar para login
    if st.button("← Voltar para Login"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()

    # Formulário de cadastro
    with st.form("cadastro_form"):
        email = st.text_input("Email")
        senha = st.text_input("Senha", type="password")
        confirmar_senha = st.text_input("Confirmar Senha", type="password")
        nome_completo = st.text_input("Nome Completo")
        data_nascimento = st.date_input("Data de Nascimento")
        cpf = st.text_input("CPF")
        telefone = st.text_input("Telefone")
        cep = st.text_input("CEP")
        endereco = st.text_input("Endereço")
        numero = st.text_input("Número")
        complemento = st.text_input("Complemento")
        bairro = st.text_input("Bairro")
        cidade = st.text_input("Cidade")
        estado = st.text_input("Estado")
        pais = st.text_input("País")

        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if senha != confirmar_senha:
                st.error("As senhas não coincidem")
                return

            try:
                # 1. Criar usuário no Firebase Auth
                user = auth.create_user(
                    email=email,
                    password=senha,
                    display_name=nome_completo
                )

                # 2. Preparar dados para o Firestore
                user_data = {
                    'uid': user.uid,
                    'email': email,
                    'nome_completo': nome_completo,
                    'data_nascimento': data_nascimento.isoformat(),
                    'cpf': cpf,
                    'telefone': telefone,
                    'endereco': {
                        'cep': cep,
                        'logradouro': endereco,
                        'numero': numero,
                        'complemento': complemento,
                        'bairro': bairro,
                        'cidade': cidade,
                        'estado': estado,
                        'pais': pais
                    },
                    'data_cadastro': firestore.SERVER_TIMESTAMP,
                    'ultimo_login': firestore.SERVER_TIMESTAMP
                }

                # 3. Salvar dados no Firestore
                db = firestore.client()
                db.collection('usuarios').document(user.uid).set(user_data)

                # 4. Atualizar session state
                st.session_state[USER_SESSION_KEY] = {
                    'uid': user.uid,
                    'email': email,
                    'display_name': nome_completo
                }
                st.session_state[AUTENTICADO_SESSION_KEY] = True
                st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'projetos'

                st.success("Cadastro realizado com sucesso!")
                st.rerun()

            except auth.EmailAlreadyExistsError:
                st.error("Este email já está cadastrado")
            except Exception as e:
                st.error(f"Erro ao cadastrar: {str(e)}")
                # Tenta remover o usuário do Auth se a criação no Firestore falhar
                try:
                    if 'user' in locals():
                        auth.delete_user(user.uid)
                except:
                    pass

def initialize_firebase_app():
    """Inicializa o Firebase Admin SDK"""
    try:
        if not firebase_admin._apps:
            firebase_admin.initialize_app()
        return True
    except Exception as e:
        st.error(f"Erro ao inicializar Firebase: {str(e)}")
        return False