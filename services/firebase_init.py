import firebase_admin
from firebase_admin import credentials
import logging
import streamlit as st
import json
from streamlit.runtime.secrets import AttrDict

_initialized = False
_error_message = None

def get_firebase_credentials():
    """Extrai e valida as credenciais do Firebase do st.secrets"""
    if not hasattr(st, 'secrets'):
        return None, "st.secrets não está disponível. Verifique se está rodando no Streamlit Cloud."

    if "firebase_credentials" not in st.secrets:
        return None, "'firebase_credentials' não encontrado em st.secrets. Verifique as configurações no Streamlit Cloud."

    raw_creds = st.secrets["firebase_credentials"]
    logging.info(f"Tipo das credenciais brutas: {type(raw_creds)}")

    # Tenta converter para dicionário se for AttrDict
    if isinstance(raw_creds, AttrDict):
        try:
            creds_dict = {
                'type': str(raw_creds.type),
                'project_id': str(raw_creds.project_id),
                'private_key_id': str(raw_creds.private_key_id),
                'private_key': str(raw_creds.private_key),
                'client_email': str(raw_creds.client_email),
                'client_id': str(raw_creds.client_id),
                'auth_uri': str(raw_creds.auth_uri),
                'token_uri': str(raw_creds.token_uri),
                'auth_provider_x509_cert_url': str(raw_creds.auth_provider_x509_cert_url),
                'client_x509_cert_url': str(raw_creds.client_x509_cert_url),
                'universe_domain': str(raw_creds.universe_domain)
            }
            return creds_dict, None
        except Exception as e:
            return None, f"Erro ao converter AttrDict para dicionário: {str(e)}"

    # Se já for dicionário, valida
    if isinstance(raw_creds, dict):
        return raw_creds, None

    # Se for string, tenta converter de JSON
    if isinstance(raw_creds, str):
        try:
            creds_dict = json.loads(raw_creds)
            return creds_dict, None
        except json.JSONDecodeError:
            return None, "Credenciais em formato string não são um JSON válido"

    return None, f"Formato de credenciais não suportado: {type(raw_creds)}"

def validate_credentials(creds_dict):
    """Valida se o dicionário de credenciais tem todos os campos necessários"""
    required_fields = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri',
        'auth_provider_x509_cert_url', 'client_x509_cert_url'
    ]

    # Verifica campos obrigatórios
    missing_fields = [field for field in required_fields if field not in creds_dict]
    if missing_fields:
        return False, f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"

    # Verifica tipo de conta
    if creds_dict.get('type') != "service_account":
        return False, f"Tipo de credencial inválido: {creds_dict.get('type')}"

    # Verifica formato da chave privada
    private_key = creds_dict.get('private_key', '')
    if not private_key:
        return False, "Chave privada não encontrada"

    # Limpa e valida a chave privada
    private_key = private_key.replace('\\n', '\n').strip()
    if not private_key.startswith('-----BEGIN PRIVATE KEY-----') or not private_key.endswith('-----END PRIVATE KEY-----'):
        return False, "Formato inválido da chave privada"

    # Atualiza a chave privada limpa
    creds_dict['private_key'] = private_key

    return True, None

def initialize_firebase():
    """Inicializa o Firebase Admin SDK com as credenciais do st.secrets"""
    global _initialized, _error_message

    if _initialized:
        return True

    try:
        if firebase_admin._apps:
            _initialized = True
            return True

        # Obtém e valida as credenciais
        creds_dict, error = get_firebase_credentials()
        if error:
            _error_message = error
            logging.error(error)
            return False

        # Valida o dicionário de credenciais
        is_valid, error = validate_credentials(creds_dict)
        if not is_valid:
            _error_message = error
            logging.error(error)
            return False

        # Inicializa o Firebase
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        _initialized = True
        logging.info("Firebase Admin SDK inicializado com sucesso")
        return True

    except Exception as e:
        _error_message = f"Erro ao inicializar Firebase: {str(e)}"
        logging.error(_error_message)
        return False

def get_error_message():
    """Retorna a mensagem de erro da última tentativa de inicialização"""
    return _error_message