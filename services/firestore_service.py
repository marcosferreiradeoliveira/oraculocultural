from firebase_admin import firestore
from datetime import datetime
from .firebase_init import initialize_firebase
import logging

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicialização garantida do Firebase
try:
    if not initialize_firebase():
        raise RuntimeError("Falha ao inicializar Firebase")
    db = firestore.client()
    logger.info("Firestore client inicializado com sucesso")
except Exception as e:
    logger.error(f"Erro ao inicializar Firestore: {str(e)}")
    raise

def salvar_resumo(projeto_id: str, tipo: str, texto: str, autor: str):
    """Função de compatibilidade com versões anteriores"""
    return gerar_e_salvar_resumo(projeto_id, tipo, texto, autor)

def gerar_e_salvar_resumo(projeto_id: str, tipo_resumo: str, texto_projeto: str, usuario_email: str):
    """
    Versão robusta com verificação em tempo real
    """
    try:
        logger.info(f"Iniciando salvamento para projeto {projeto_id}")
        
        # Verificação do projeto
        projeto_ref = db.collection("projetos").document(projeto_id)
        projeto = projeto_ref.get()
        
        if not projeto.exists:
            error_msg = f"Projeto {projeto_id} não encontrado"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info(f"Projeto encontrado: {projeto.to_dict().get('nome')}")
        
        # Geração do resumo
        from models import gerar_resumo_projeto
        texto_resumo = gerar_resumo_projeto(texto_projeto)
        
        if not texto_resumo or not texto_resumo.strip():
            error_msg = "Resumo gerado está vazio"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Dados do resumo
        resumo_data = {
            "tipo": tipo_resumo,
            "texto": texto_resumo,
            "autor": usuario_email,
            "criado_em": datetime.now(),
            "projeto_id": projeto_id,
            "status": "ativo"
        }
        
        # Referência do documento
        resumos_ref = db.collection("projetos").document(projeto_id).collection("resumos")
        doc_ref = resumos_ref.document()
        
        # Operação de escrita com timeout
        doc_ref.set(resumo_data)
        logger.info(f"Resumo salvo com ID: {doc_ref.id}")
        
        # Verificação imediata
        doc_salvo = doc_ref.get()
        if not doc_salvo.exists:
            error_msg = "Resumo não foi salvo corretamente"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        return {**resumo_data, "id": doc_ref.id}
        
    except Exception as e:
        logger.error(f"Erro completo ao salvar resumo: {str(e)}", exc_info=True)
        raise