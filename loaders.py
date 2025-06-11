import os
from time import sleep
import streamlit as st
from langchain_community.document_loaders import (WebBaseLoader,
                                                  YoutubeLoader, 
                                                  CSVLoader, 
                                                  PyPDFLoader, 
                                                  TextLoader)
from fake_useragent import UserAgent

def carrega_site(url):
    documento = ''
    for i in range(5):
        try:
            os.environ['USER_AGENT'] = UserAgent().random
            loader = WebBaseLoader(url, raise_for_status=True)
            lista_documentos = loader.load()
            documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
            break
        except:
            print(f'Erro ao carregar o site {i+1}')
            sleep(3)
    if documento == '':
        st.error('Não foi possível carregar o site')
        st.stop()
    return documento

def carrega_youtube(video_id):
    loader = YoutubeLoader(video_id, add_video_info=False, language=['pt'])
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_csv(caminho):
    loader = CSVLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento

def carrega_pdf(caminho):
    """Carrega e extrai texto de um arquivo PDF com tratamento de erros robusto"""
    try:
        # Tenta primeiro com PyPDFLoader
        try:
            loader = PyPDFLoader(caminho)
            lista_documentos = loader.load()
            # Mantém parágrafos separados por duas quebras de linha
            documento = '\n\n'.join([doc.page_content.replace('\n', ' ').strip() for doc in lista_documentos])
            if documento and len(documento.strip()) > 10:
                return documento
        except Exception as e:
            print(f"PyPDFLoader falhou: {str(e)}")
            # Se falhar, continua para tentar outros métodos

        # Se PyPDFLoader falhar ou retornar texto vazio, tenta com pypdf diretamente
        try:
            import pypdf
            reader = pypdf.PdfReader(caminho)
            texto = ""
            for page in reader.pages:
                # Mantém parágrafos separados por duas quebras de linha
                texto += page.extract_text().replace('\n', ' ').strip() + "\n\n"
            if texto and len(texto.strip()) > 10:
                return texto.strip()
        except Exception as e:
            print(f"pypdf falhou: {str(e)}")
            # Se falhar, continua para tentar outros métodos

        # Se ainda não conseguiu, tenta com pdfplumber
        try:
            import pdfplumber
            with pdfplumber.open(caminho) as pdf:
                texto = ""
                for page in pdf.pages:
                    # Mantém parágrafos separados por duas quebras de linha
                    texto += page.extract_text().replace('\n', ' ').strip() + "\n\n"
                if texto and len(texto.strip()) > 10:
                    return texto.strip()
        except Exception as e:
            print(f"pdfplumber falhou: {str(e)}")

        # Se nenhum método funcionou, retorna erro
        raise Exception("Não foi possível extrair texto do PDF usando nenhum dos métodos disponíveis. O arquivo pode estar corrompido, protegido por senha ou conter apenas imagens.")

    except Exception as e:
        error_msg = str(e)
        if "password" in error_msg.lower():
            raise Exception("O PDF está protegido por senha. Por favor, remova a proteção e tente novamente.")
        elif "not a PDF" in error_msg.lower():
            raise Exception("O arquivo não parece ser um PDF válido.")
        elif "corrupted" in error_msg.lower():
            raise Exception("O arquivo PDF parece estar corrompido.")
        else:
            raise Exception(f"Erro ao processar PDF: {error_msg}")

def carrega_txt(caminho):
    loader = TextLoader(caminho)
    lista_documentos = loader.load()
    documento = '\n\n'.join([doc.page_content for doc in lista_documentos])
    return documento
