from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

# Configuração otimizada do LLM com cache
@st.cache_resource
def get_llm(model="gpt-4-turbo", temperature=0.7, max_tokens=2000):
    """Retorna uma instância configurada do LLM com cache"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=st.secrets["openai"]["api_key"],
        streaming=True  # Habilita streaming para respostas longas
    )

# Função base para criação de chains
def _create_chain(prompt_template, llm=None, diagnostico=None):
    """Factory method para criar chains padronizadas"""
    llm = llm or get_llm()
    
    # Tratamento condicional do diagnóstico
    if diagnostico:
        prompt_template = f"CONTEXTO ADICIONAL:\n{diagnostico}\n\n{prompt_template}"
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    return (
        RunnablePassthrough()
        | prompt
        | llm
        | StrOutputParser()
    )

def gerar_resumo_projeto(texto_projeto, diagnostico=None, llm=None):
    """Gera resumo executivo do projeto cultural"""
    template = """
    Gere um resumo profissional (150-200 palavras) com:
    - Objetivos claros
    - Público-alvo definido
    - Metodologia concisa
    - Impacto cultural esperado
    
    PROJETO:
    {texto}
    
    FORMATE EM MARKDOWN COM SEÇÕES CLARAS"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})  # Limite seguro de tokens

def gerar_orcamento(texto_projeto, diagnostico=None, llm=None):
    """Gera orçamento detalhado em formato tabular"""
    template = """
    Gere um orçamento detalhado com:
    1. MATERIAIS (itens, quantidades, valores unitários e totais)
    2. PESSOAL (funções, carga horária, valores/hora e totais)
    3. INFRAESTRUTURA (itens, períodos, valores)
    4. OUTRAS DESPESAS (descrição e valores)
    5. TOTAL GERAL consolidado
    
    FORMATE COMO TABELA MARKDOWN
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})

def gerar_cronograma(texto_projeto, diagnostico=None, llm=None):
    """Gera cronograma com marcos temporais"""
    template = """
    Crie um cronograma com:
    - FASES PRINCIPAIS (planejamento, execução, finalização)
    - ATIVIDADES por fase
    - PRAZOS ESTIMADOS (datas ou durações)
    - RESPONSÁVEIS
    
    USE FORMATO DE LISTA MARKDOWN COM DATAS
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})

def gerar_objetivos(texto_projeto, diagnostico=None, llm=None):
    """Formula objetivos no padrão SMART"""
    template = """
    Reformule os objetivos como SMART:
    [ESPECÍFICO] - O quê exatamente será feito?
    [MENSURÁVEL] - Como medir o sucesso?
    [ATINGÍVEL] - É realista com os recursos?
    [RELEVANTE] - Alinhamento com metas maiores?
    [TEMPORAL] - Qual o prazo final?
    
    NUMERE E FORMATE CLARAMENTE
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})

def gerar_justificativa(texto_projeto, diagnostico=None, llm=None):
    """Elabora justificativa técnica"""
    template = """
    Desenvolva uma justificativa com:
    1. CONTEXTO CULTURAL (por que é importante?)
    2. INOVAÇÃO (o que traz de novo?)
    3. IMPACTO SOCIAL (benefícios para quem?)
    4. VIABILIDADE (por que pode dar certo?)
    
    USE PARÁGRAFOS COESOS E ARGUMENTATIVOS
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})

def gerar_etapas_trabalho(texto_projeto, diagnostico=None, llm=None):
    """Detalha etapas de execução"""
    template = """
    Descreva as etapas com:
    [PLANEJAMENTO]
    - Tarefas específicas
    - Responsáveis
    - Pré-requisitos
    
    [EXECUÇÃO]
    - Fluxo operacional
    - Marcos críticos
    - Indicadores de progresso
    
    [AVALIAÇÃO]
    - Métricas de sucesso
    - Ferramentas de análise
    
    FORMATE COM LISTAS HIERARQUICAS
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})

def gerar_ficha_tecnica(texto_projeto, diagnostico=None, llm=None):
    """Produz ficha técnica completa"""
    template = """
    Crie uma ficha técnica contendo:
    [EQUIPE]
    - Função | Responsabilidades | Qualificações | Vínculo
    
    [RECURSOS]
    - Equipamentos | Especificações | Quantidade
    - Espaços | Requisitos | Período
    - Materiais | Tipos | Quantidades
    
    FORMATE COMO TABELAS MARKDOWN
    
    PROJETO:
    {texto}"""
    
    chain = _create_chain(template, llm, diagnostico)
    return chain.invoke({"texto": texto_projeto[:15000]})