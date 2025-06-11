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

def welcome_popup():
    """Creates a welcome popup that explains the platform's workflow"""
    st.markdown("""
        <style>
            .welcome-popup {
                background-color: white;
                border-radius: 12px;
                padding: 2rem;
                box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
                margin-bottom: 2rem;
            }
            .welcome-popup h2 {
                color: #1e293b;
                font-family: 'Playfair Display', serif;
                font-size: 1.8rem;
                margin-bottom: 1rem;
            }
            .welcome-popup p {
                color: #475569;
                font-size: 1rem;
                line-height: 1.6;
                margin-bottom: 1rem;
            }
            .welcome-popup .step {
                display: flex;
                align-items: flex-start;
                margin-bottom: 1rem;
                gap: 1rem;
            }
            .welcome-popup .step-number {
                background-color: #7e22ce;
                color: white;
                width: 24px;
                height: 24px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                flex-shrink: 0;
            }
            .welcome-popup .step-content {
                flex-grow: 1;
            }
        </style>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="welcome-popup">
            <h2>Bem-vindo ao Oráculo Cultural! 🎭</h2>
            <p>Vamos te ajudar a criar um projeto cultural de sucesso. Siga estes passos:</p>
            
            <div class="step">
                <div class="step-number">1</div>
                <div class="step-content">
                    <strong>Crie um novo projeto</strong>
                    <p>Comece criando um novo projeto na plataforma</p>
                </div>
            </div>
            
            <div class="step">
                <div class="step-number">2</div>
                <div class="step-content">
                    <strong>Selecione um edital</strong>
                    <p>Escolha o edital para o qual você deseja se inscrever</p>
                </div>
            </div>
            
            <div class="step">
                <div class="step-number">3</div>
                <div class="step-content">
                    <strong>Insira seu rascunho</strong>
                    <p>Adicione o primeiro rascunho do seu projeto para avaliação</p>
                </div>
            </div>
            
            <div class="step">
                <div class="step-number">4</div>
                <div class="step-content">
                    <strong>Receba feedback da IA</strong>
                    <p>Nossa IA analisará seu projeto com base nos critérios do edital e no perfil dos projetos selecionados anteriormente</p>
                </div>
            </div>
            
            <div class="step">
                <div class="step-number">5</div>
                <div class="step-content">
                    <strong>Gere textos otimizados</strong>
                    <p>Use a IA para gerar textos como justificativa, objetivo, orçamento e cronograma adequados ao perfil do edital</p>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)