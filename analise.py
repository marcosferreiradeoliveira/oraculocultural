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

def avaliar_contra_edital(texto_projeto, texto_edital=None, texto_selecionados=None):
    """Avalia o projeto contra os critérios do edital, opcionalmente usando textos de edital e selecionados fornecidos."""
    try:
        # Use texto_edital fornecido ou carregue o padrão se nenhum for dado
        edital_context = texto_edital if texto_edital is not None else carregar_documento_edital()
        selecionados_context = texto_selecionados if texto_selecionados is not None else carregar_projetos_selecionados() # Usado como contexto adicional

        prompt_template = """Você é um avaliador de projetos culturais. Analise o projeto abaixo:

PROJETO:
{projeto}

Considerando:
CRITÉRIOS DO EDITAL:
{edital}

PROJETOS SELECIONADOS ANTERIORES (para contexto comparativo):
{selecionados}

Forneça uma análise detalhada com:
1. Adequação aos critérios do edital (✅/❌)
2. Pontos fortes do projeto
3. Pontos fracos do projeto
4. Sugestões de melhoria: Liste as sugestões para aumentar a chance de aprovação, cada uma começando explicitamente com "Sugestão: ".
5. Nota estimada (0-100)

ANÁLISE DETALHADA:"""

        prompt = ChatPromptTemplate.from_template(prompt_template)

        chain = prompt | llm | StrOutputParser()
        return chain.invoke({
            "edital": edital_context[:15000] if edital_context else "Nenhum texto de edital fornecido.",  # Limita e trata None
            "selecionados": selecionados_context[:20000] if selecionados_context else "Nenhum texto de projetos selecionados fornecido.", # Limita e trata None
            "projeto": texto_projeto[:10000]
        })

    except Exception as e:
        return f"Erro na análise contra edital: {str(e)}"

def comparar_com_selecionados(texto_projeto, texto_edital=None, texto_selecionados=None):
    """Compara o projeto com os selecionados anteriores, opcionalmente usando textos de edital e selecionados fornecidos."""
    # Use texto_selecionados fornecido ou carregue o padrão se nenhum for dado
    selecionados_context = texto_selecionados if texto_selecionados is not None else carregar_projetos_selecionados()
    edital_context = texto_edital if texto_edital is not None else carregar_documento_edital() # Usado como contexto adicional

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
        4. Recomendações para aumentar chances: Liste as recomendações, cada uma começando com "Sugestão: ".
        
        Análise comparativa:"""
    )
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({
        "selecionados": texto_selecionados[:20000],
        "projeto": texto_projeto[:10000]
    })

     