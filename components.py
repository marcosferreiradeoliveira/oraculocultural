import streamlit as st
import tempfile
from loaders import carrega_pdf, carrega_csv, carrega_txt  # Importação explícita

def file_uploader(file_types, key=None, label="Envie seu arquivo"):
    """
    Componente genérico para upload de arquivos
    Parâmetros:
    - file_types: Lista de extensões permitidas (['pdf'], ['csv', 'txt'], etc.)
    - key: Chave única para o componente Streamlit
    - label: Rótulo personalizado
    Retorna: (tipo_arquivo, conteúdo_extraído) ou (None, None)
    """
    file = st.file_uploader(
        label,
        type=file_types,
        accept_multiple_files=False,
        key=key
    )
    
    if not file:
        return None, None
    
    # Obtém a extensão do arquivo
    file_extension = file.name.split('.')[-1].lower()
    
    try:
        with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp:
            temp.write(file.read())
            temp_path = temp.name
        
        # Processa conforme o tipo de arquivo
        if file_extension == 'pdf':
            return 'Pdf', carrega_pdf(temp_path)
        elif file_extension == 'csv':
            return 'Csv', carrega_csv(temp_path)
        elif file_extension == 'txt':
            return 'Txt', carrega_txt(temp_path)
            
    except Exception as e:
        st.error(f"Erro ao processar arquivo: {str(e)}")
        return None, None
    
    return None, None