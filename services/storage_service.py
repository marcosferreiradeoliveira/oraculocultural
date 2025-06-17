import firebase_admin
from firebase_admin import storage
import tempfile
import os
from .firebase_init import initialize_firebase, get_storage_bucket
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Variável global para o bucket
_bucket = None

def get_or_create_bucket():
    """
    Obtém ou cria o bucket do Storage se não existir
    """
    global _bucket
    
    # Se já temos um bucket, retorna ele
    if _bucket is not None:
        return _bucket
        
    try:
        if not initialize_firebase():
            raise RuntimeError("Falha ao inicializar Firebase")
        
        # Obtém o bucket do Storage
        storage_bucket = get_storage_bucket()
        if not storage_bucket:
            raise RuntimeError("Nome do bucket do Storage não encontrado")
        
        try:
            bucket = storage.bucket(storage_bucket)
            # Tenta acessar o bucket para verificar se existe
            bucket.exists()
            logger.info(f"Bucket {storage_bucket} encontrado")
            _bucket = bucket
            return _bucket
        except Exception as e:
            logger.warning(f"Bucket {storage_bucket} não encontrado. Tentando criar...")
            # Tenta criar o bucket
            bucket = storage.bucket(storage_bucket)
            bucket.create()
            logger.info(f"Bucket {storage_bucket} criado com sucesso")
            _bucket = bucket
            return _bucket
            
    except Exception as e:
        logger.error(f"Erro ao inicializar/criar bucket do Storage: {str(e)}")
        raise

def upload_file(file_data, destination_path, content_type=None):
    """
    Faz upload de um arquivo para o Firebase Storage
    
    Args:
        file_data: Bytes do arquivo ou caminho do arquivo
        destination_path: Caminho de destino no storage (ex: 'editais/modelos/carta_anuencia.pdf')
        content_type: Tipo MIME do arquivo (opcional)
    
    Returns:
        dict: Dicionário com informações do upload (url, path, etc)
    """
    try:
        # Obtém o bucket
        bucket = get_or_create_bucket()
        
        # Cria um blob no bucket
        blob = bucket.blob(destination_path)
        
        # Se file_data for bytes, faz upload direto
        if isinstance(file_data, bytes):
            blob.upload_from_string(
                file_data,
                content_type=content_type
            )
        # Se for caminho de arquivo, faz upload do arquivo
        elif isinstance(file_data, str) and os.path.exists(file_data):
            blob.upload_from_filename(file_data)
        else:
            raise ValueError("file_data deve ser bytes ou caminho de arquivo válido")
        
        # Gera URL pública
        blob.make_public()
        
        return {
            'url': blob.public_url,
            'path': destination_path,
            'content_type': blob.content_type,
            'size': blob.size
        }
        
    except Exception as e:
        logger.error(f"Erro ao fazer upload do arquivo: {str(e)}")
        raise

def delete_file(storage_path):
    """
    Deleta um arquivo do Firebase Storage
    
    Args:
        storage_path: Caminho do arquivo no storage
    """
    try:
        # Obtém o bucket
        bucket = get_or_create_bucket()
        
        blob = bucket.blob(storage_path)
        blob.delete()
        logger.info(f"Arquivo {storage_path} deletado com sucesso")
    except Exception as e:
        logger.error(f"Erro ao deletar arquivo {storage_path}: {str(e)}")
        raise

def get_file_url(storage_path):
    """
    Obtém a URL pública de um arquivo no storage
    
    Args:
        storage_path: Caminho do arquivo no storage
    
    Returns:
        str: URL pública do arquivo
    """
    try:
        # Obtém o bucket
        bucket = get_or_create_bucket()
        
        blob = bucket.blob(storage_path)
        return blob.public_url
    except Exception as e:
        logger.error(f"Erro ao obter URL do arquivo {storage_path}: {str(e)}")
        raise 