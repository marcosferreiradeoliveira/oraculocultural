import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from loaders import carrega_pdf  # Adicione no topo do arquivo
from models import get_llm  # Importa a função que cria o modelo LLM
import streamlit as st  # Esta é a linha crucial que estava faltando


llm = get_llm() 

@st.cache_data
def carregar_documento_edital():
    """Carrega o texto do edital oficial com tratamento de erros"""
    try:
        caminho_edital = "docs/REGULAMENTO-CHAMADA-INSTITUTO-CULTURAL-VALE-2025-Revisao-Final.pdf"
        return carrega_pdf(caminho_edital)
    except Exception as e:
        st.error(f"Erro ao carregar edital: {str(e)}")
        st.stop()

@st.cache_data
def carregar_projetos_selecionados():
    """Carrega a lista de projetos selecionados com tratamento de erros"""
    try:
        caminho_selecionados = "docs/Edital Vale_ Análise dos Selecionados_.pdf"
        return carrega_pdf(caminho_selecionados)
    except Exception as e:
        st.error(f"Erro ao carregar projetos selecionados: {str(e)}")
        st.stop()
def gerar_orcamento(llm, texto_projeto):
    prompt = ChatPromptTemplate.from_template(
        """Com base no projeto abaixo, gere uma proposta de orçamento detalhada incluindo:
        - Recursos humanos
        - Materiais
        - Serviços terceirizados
        - Custos administrativos
        - Reserva técnica (10%)
        
        PROJETO:
        {texto}
        
        ORÇAMENTO PROPOSTO:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"texto": texto_projeto[:10000]})

def gerar_cronograma(llm, texto_projeto):
    prompt = ChatPromptTemplate.from_template(
        """Crie um cronograma de 12 meses para o projeto abaixo, com:
        - Fases principais
        - Marcos importantes
        - Atividades mensais
        - Entregas esperadas
        
        PROJETO:
        {texto}
        
        CRONOGRAMA:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"texto": texto_projeto[:10000]})

def gerar_justificativa(llm, texto_projeto):
    prompt = ChatPromptTemplate.from_template(
        """Elabore uma justificativa técnica para o projeto contendo:
        1. Relevância cultural
        2. Originalidade
        3. Viabilidade técnica
        4. Impacto social esperado
        
        PROJETO:
        {texto}
        
        JUSTIFICATIVA TÉCNICA:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"texto": texto_projeto[:10000]})

def gerar_objetivos(llm, texto_projeto):
    prompt = ChatPromptTemplate.from_template(
        """Reformule os objetivos do projeto seguindo a metodologia SMART:
        - Específicos
        - Mensuráveis
        - Atingíveis
        - Relevantes
        - Temporais
        
        PROJETO:
        {texto}
        
        OBJETIVOS SMART:"""
    )
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"texto": texto_projeto[:10000]})

def avaliar_contra_edital(texto_projeto):
    """Avalia o projeto contra os critérios do edital"""
    try:
        texto_edital = carregar_documento_edital()
        
        prompt = ChatPromptTemplate.from_template(
            """Você é um avaliador de projetos culturais. Analise este projeto:
            
            PROJETO:
            {projeto}
            
            Considerando estes CRITÉRIOS DO EDITAL:
            {edital}
            
            Forneça uma análise detalhada com:
            1. Adequação aos critérios (✅/❌)
            2. Pontos fortes
            3. Pontos fracos
            4. Sugestões de melhoria
            5. Nota estimada (0-100)
            
            ANÁLISE:"""
        )
        
        chain = prompt | llm | StrOutputParser()
        return chain.invoke({
            "edital": texto_edital[:15000],  # Limita o tamanho
            "projeto": texto_projeto[:10000]
        })
    
    except Exception as e:
        return f"Erro na análise: {str(e)}"
def comparar_com_selecionados(texto_projeto):
    """Compara o projeto com os selecionados anteriores"""
    texto_selecionados = carregar_projetos_selecionados()
    
    prompt = ChatPromptTemplate.from_template(
        """Analise este projeto em comparação com projetos selecionados
        em editais anteriores:
        
        PROJETOS SELECIONADOS ANTERIORES:
        {selecionados}
        
        NOVO PROJETO:
        {projeto}
        
        Forneça:
        1. Semelhanças com projetos aprovados
        2. Diferenças notáveis
        3. Fatores competitivos
        4. Recomendações para aumentar chances
        
        Análise comparativa:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "selecionados": texto_selecionados[:20000],
        "projeto": texto_projeto[:10000]
    })

     