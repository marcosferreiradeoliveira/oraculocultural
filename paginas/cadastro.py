import streamlit as st
import firebase_admin
from firebase_admin import auth, firestore, credentials
from constants import PAGINA_ATUAL_SESSION_KEY
from services.firebase_init import initialize_firebase, get_error_message

# É uma boa prática verificar se o Firebase Admin já foi inicializado,
# especialmente se este código puder ser chamado em diferentes contextos.
# No entanto, a inicialização principal geralmente ocorre no script principal do seu app.
# Se este for um módulo de página isolado, garanta que a inicialização ocorreu antes.
# Para este exemplo, vamos assumir que a inicialização já aconteceu ou adicionar um bloco simples.

try:
    if not firebase_admin._apps:
        if not initialize_firebase():
            st.error(get_error_message())
            db = None
        else:
            db = firestore.client()
except Exception as e:
    if "already initialized" not in str(e).lower(): # Ignora erro de já inicializado
        st.error(f"Falha ao inicializar Firebase Admin (necessário para Firestore): {e}")
        print(f"Erro de inicialização Firebase em pagina_cadastro: {e}")
    db = None 
    print(f"Firestore client não pôde ser obtido em pagina_cadastro: {e}")


def pagina_cadastro():
    st.markdown("""
        <style>
            .cadastro-container {
                max-width: 400px;
                margin: 2rem auto;
                padding: 2rem;
                background: white;
                border-radius: 1rem;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            .cadastro-title {
                color: #1e293b;
                font-size: 1.5rem;
                font-weight: 600;
                margin-bottom: 1rem;
                text-align: center;
            }
            .cadastro-description {
                color: #64748b;
                margin-bottom: 2rem;
                text-align: center;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="cadastro-container">', unsafe_allow_html=True)
    st.markdown('''<div style="text-align:center; margin-bottom: 1.5rem;">
        <img src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='80' height='80' viewBox='0 0 24 24' fill='none' stroke='%237e22ce' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cpath d='M12 16c2.2 0 4-1.8 4-4s-1.8-4-4-4-4 1.8-4 4 1.8 4 4 4z'%3E%3C/path%3E%3Cpath d='M12 8v-2'%3E%3C/path%3E%3Cpath d='M12 18v-2'%3E%3C/path%3E%3Cpath d='M8 12h-2'%3E%3C/path%3E%3Cpath d='M18 12h-2'%3E%3C/path%3E%3C/svg%3E" alt="Oráculo Cultural Logo" style="width:80px;height:80px;"/>
    </div>''', unsafe_allow_html=True)
    st.markdown('<h2 class="cadastro-title">Cadastre-se</h2>', unsafe_allow_html=True)
    st.markdown('<p class="cadastro-description">Preencha os campos abaixo para criar sua conta.</p>', unsafe_allow_html=True)

    with st.form("cadastro_form"):
        email = st.text_input("Email", placeholder="seu@email.com")
        nome = st.text_input("Nome completo")
        empresa = st.text_input("Nome da empresa (Opcional)") # Tornando opcional como exemplo
        senha = st.text_input("Senha", type="password")
        repetir_senha = st.text_input("Repetir senha", type="password")
        submitted = st.form_submit_button("Cadastrar")

        if submitted:
            if not email or not nome or not senha or not repetir_senha: # Empresa pode ser opcional
                st.error("Por favor, preencha todos os campos obrigatórios (Email, Nome, Senha, Repetir Senha).")
            elif len(senha) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif senha != repetir_senha:
                st.error("As senhas não coincidem.")
            elif not db: # Verifica se o cliente Firestore está disponível
                st.error("Não foi possível conectar ao banco de dados para salvar informações adicionais. Cadastro não pôde ser completado.")
            else:
                try:
                    # 1. Criar usuário no Firebase Authentication
                    user_record = auth.create_user(
                        email=email,
                        password=senha,
                        display_name=nome
                    )
                    st.toast(f"Usuário {user_record.email} autenticado com sucesso!", icon="🔑")

                    # 2. Preparar dados para o Firestore
                    user_data = {
                        'uid': user_record.uid,
                        'email': user_record.email,
                        'nome': nome, # ou user_record.display_name
                        'empresa': empresa if empresa else '', # Salva vazio se não preenchido
                        'premium': False,
                        'data_cadastro': firestore.SERVER_TIMESTAMP, # Data de criação no Firestore
                        'ultimo_login': firestore.SERVER_TIMESTAMP # Pode ser atualizado no login
                    }

                    # 3. Salvar dados no Firestore na coleção 'usuarios' (ou 'users')
                    # O ID do documento será o UID do usuário para fácil vinculação
                    db.collection('usuarios').document(user_record.uid).set(user_data)
                    
                    st.toast("Seu perfil foi criado no banco de dados!", icon="📄")
                    st.success("Cadastro efetuado com sucesso! Você será redirecionado para o login.")
                    
                    # Definir um pequeno atraso para o usuário ler as mensagens antes do rerun
                    import time
                    time.sleep(2) 
                    
                    st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
                    st.rerun()

                except firebase_admin.auth.EmailAlreadyExistsError:
                    st.error("Este email já está cadastrado. Tente fazer login ou use um email diferente.")
                except Exception as e:
                    # Se ocorrer um erro após a criação do usuário no Auth mas antes de salvar no Firestore,
                    # o usuário no Auth pode precisar ser removido manualmente ou por uma função de cleanup,
                    # dependendo da sua política de consistência de dados.
                    st.error(f"Erro ao cadastrar: {str(e)}")
                    # Tenta remover o usuário do Auth se a criação no Firestore falhar, como uma tentativa de rollback.
                    # Isso é opcional e pode ter suas próprias falhas.
                    if 'user_record' in locals() and user_record:
                        try:
                            auth.delete_user(user_record.uid)
                            st.warning("Tentativa de rollback: usuário removido do sistema de autenticação devido a erro subsequente.")
                        except Exception as delete_error:
                            st.error(f"Erro adicional ao tentar remover usuário do Auth após falha: {delete_error}")


    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("⬅️ Voltar para Login"):
        st.session_state[PAGINA_ATUAL_SESSION_KEY] = 'login'
        st.rerun()