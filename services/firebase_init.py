import firebase_admin
from firebase_admin import credentials
import logging
import streamlit as st
import json
import os
from streamlit.runtime.secrets import AttrDict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_initialized = False
_error_message = None

def get_firebase_credentials():
    """Extrai e valida as credenciais do Firebase do st.secrets ou arquivo local"""
    # Primeiro tenta arquivo local (ambiente de desenvolvimento)
    # Tenta diferentes caminhos possíveis para o arquivo de credenciais
    possible_paths = [
        "config/firebase-service-account.json",  # Caminho relativo
        os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "firebase-service-account.json"),  # Caminho relativo ao módulo
        "/Users/marcosferreira/Documents/Cultural/cultural/config/firebase-service-account.json"  # Caminho absoluto
    ]
    
    for local_cred_path in possible_paths:
        logger.info(f"Tentando ler credenciais do arquivo: {local_cred_path}")
        if os.path.exists(local_cred_path):
            try:
                logger.info(f"Arquivo encontrado em: {local_cred_path}")
                with open(local_cred_path, 'r') as f:
                    creds_dict = json.load(f)
                logger.info("Credenciais carregadas com sucesso do arquivo local")
                return creds_dict, None
            except Exception as e:
                logger.error(f"Erro ao ler arquivo de credenciais local: {str(e)}")
                continue

    # Se não encontrou arquivo local, tenta st.secrets (ambiente de produção)
    try:
        if hasattr(st, 'secrets') and "firebase_credentials" in st.secrets:
            raw_creds = st.secrets["firebase_credentials"]
            logger.info("Usando credenciais do st.secrets (ambiente de produção)")
            
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
    except Exception as e:
        # Ignora erros de st.secrets em ambiente local
        logger.info("st.secrets não disponível (ambiente local)")

    return None, (
        "Nenhuma credencial do Firebase encontrada. "
        "Para desenvolvimento local, coloque o arquivo 'firebase-service-account.json' em 'config/'. "
        "Para produção, configure as credenciais no Streamlit Cloud."
    )

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

def get_storage_bucket():
    """Obtém o nome do bucket do Storage do Firebase"""
    # Bucket padrão para o projeto
    DEFAULT_BUCKET = "culturalapp-fb9b0.firebasestorage.app"
    
    # Tenta obter do arquivo de credenciais
    creds_dict, _ = get_firebase_credentials()
    if creds_dict and 'project_id' in creds_dict:
        return DEFAULT_BUCKET
    
    # Tenta obter do st.secrets
    if hasattr(st, 'secrets'):
        if "firebase" in st.secrets and "storage_bucket" in st.secrets.firebase:
            return st.secrets.firebase.storage_bucket
    
    # Retorna o bucket padrão se nada mais for encontrado
    return DEFAULT_BUCKET

def initialize_firebase():
    """Inicializa o Firebase Admin SDK com as credenciais apropriadas"""
    global _initialized, _error_message

    if _initialized:
        logger.info("Firebase já inicializado")
        return True

    try:
        if firebase_admin._apps:
            _initialized = True
            logger.info("Firebase já inicializado (firebase_admin._apps existe)")
            return True

        # Obtém e valida as credenciais
        logger.info("Tentando obter credenciais do Firebase...")
        creds_dict, error = get_firebase_credentials()
        if error:
            _error_message = error
            logger.error(f"Erro ao obter credenciais: {error}")
            return False

        # Obtém o nome do bucket
        storage_bucket = get_storage_bucket()
        if not storage_bucket:
            _error_message = "Nome do bucket do Storage não encontrado"
            logger.error(_error_message)
            return False

        # Inicializa o Firebase com as configurações do Storage
        logger.info("Inicializando Firebase Admin SDK...")
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': storage_bucket
        })
        _initialized = True
        logger.info("Firebase Admin SDK inicializado com sucesso")
        return True

    except Exception as e:
        _error_message = f"Erro ao inicializar Firebase: {str(e)}"
        logger.error(_error_message)
        return False

def get_error_message():
    """Retorna a mensagem de erro da última tentativa de inicialização"""
    return _error_message