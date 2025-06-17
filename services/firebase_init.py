import firebase_admin
from firebase_admin import credentials, firestore
import logging
import json
import os
from services.env_manager import get_env_value
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variáveis globais para controle de estado
_initialized = False
_error_message = None
_db = None

def get_firebase_credentials():
    """Obtém as credenciais do Firebase do ambiente"""
    try:
        # Tenta obter as credenciais do ambiente
        creds_json = os.getenv('FIREBASE_CREDENTIALS')
        logger.info("Tentando obter credenciais do Firebase...")
        
        if not creds_json:
            logger.error("FIREBASE_CREDENTIALS não encontrado nas variáveis de ambiente")
            logger.debug("Variáveis de ambiente disponíveis: %s", list(os.environ.keys()))
            return None
            
        # Converte a string JSON em um dicionário
        try:
            logger.info("Tentando decodificar JSON das credenciais...")
            creds_dict = json.loads(creds_json)
            logger.info("JSON decodificado com sucesso")
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON das credenciais: {str(e)}")
            logger.debug("Primeiros 100 caracteres do JSON: %s", creds_json[:100] if creds_json else "None")
            return None
            
        # Valida as credenciais
        logger.info("Validando estrutura das credenciais...")
        is_valid, error_msg = validate_credentials(creds_dict)
        if not is_valid:
            logger.error(f"Credenciais inválidas: {error_msg}")
            return None
            
        logger.info("Credenciais do Firebase validadas com sucesso")
        return creds_dict
        
    except Exception as e:
        logger.error(f"Erro ao obter credenciais do Firebase: {str(e)}")
        logger.exception("Stack trace completo:")
        return None

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
        # Verifica se já existe uma instância do Firebase
        if firebase_admin._apps:
            _initialized = True
            _db = firestore.client()
            return True
            
        # Obtém as credenciais do Firebase
        creds_dict = get_firebase_credentials()
        
        if not creds_dict:
            _error_message = "Credenciais do Firebase não encontradas"
            return False
            
        # Inicializa o Firebase Admin SDK
        cred = credentials.Certificate(creds_dict)
        firebase_admin.initialize_app(cred, {
            'storageBucket': creds_dict.get('storageBucket')
        })
        
        # Inicializa o cliente Firestore
        _db = firestore.client()
        _initialized = True
        return True
        
    except Exception as e:
        _error_message = str(e)
        return False

def get_error_message():
    """Retorna a mensagem de erro da última tentativa de inicialização"""
    return _error_message

def get_db():
    """Retorna o cliente Firestore inicializado"""
    if not _initialized:
        if not initialize_firebase():
            raise RuntimeError(f"Falha ao inicializar Firebase: {_error_message}")
    return _db