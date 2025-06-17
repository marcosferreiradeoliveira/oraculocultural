import firebase_admin
from firebase_admin import credentials, firestore
import logging
import json
import os
from services.env_manager import get_env_value

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

_initialized = False
_error_message = None
_db = None

def get_firebase_credentials():
    """Extrai e valida as credenciais do Firebase do ambiente Railway ou arquivo local"""
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

    # Se não encontrou arquivo local, tenta do ambiente Railway
    try:
        creds_dict = get_env_value("firebase_credentials")
        if creds_dict:
            logger.info("Usando credenciais do ambiente Railway")
            return creds_dict, None
    except Exception as e:
        logger.error(f"Erro ao ler credenciais do ambiente Railway: {str(e)}")

    return None, (
        "Nenhuma credencial do Firebase encontrada. "
        "Para desenvolvimento local, coloque o arquivo 'firebase-service-account.json' em 'config/'. "
        "Para produção, configure as credenciais no Railway."
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
    
    # Retorna o bucket padrão se nada mais for encontrado
    return DEFAULT_BUCKET

def initialize_firebase():
    """Inicializa o Firebase Admin SDK"""
    global _initialized, _error_message, _db
    
    if _initialized:
        return True
        
    try:
        creds_dict, error = get_firebase_credentials()
        if error:
            _error_message = error
            return False
            
        if not creds_dict:
            _error_message = "Credenciais do Firebase não encontradas"
            return False
            
        # Inicializa o Firebase Admin SDK
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred)
        
        # Inicializa o cliente Firestore
        _db = firestore.client()
        
        _initialized = True
        logger.info("Firebase Admin SDK e Firestore inicializados com sucesso")
        return True
    except Exception as e:
        _error_message = f"Erro ao inicializar Firebase: {str(e)}"
        logger.error(_error_message)
        return False

def get_firestore_client():
    """Retorna o cliente Firestore inicializado"""
    global _db
    
    if not _initialized:
        if not initialize_firebase():
            raise RuntimeError(f"Falha ao inicializar Firebase: {_error_message}")
    
    if not _db:
        _db = firestore.client()
    
    return _db

def get_error_message():
    """Retorna a mensagem de erro da última tentativa de inicialização"""
    return _error_message