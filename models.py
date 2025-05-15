from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
import streamlit as st
from typing import Optional, Dict, Any

# Configuração centralizada do LLM
@st.cache_resource
def get_llm(
    model: str = "gpt-4-turbo",
    temperature: float = 0.7,
    max_tokens: int = 2000
) -> ChatOpenAI:
    """Retorna uma instância configurada do ChatOpenAI com cache.
    
    Args:
        model: Modelo a ser utilizado (padrão: 'gpt-4-turbo')
        temperature: Criatividade das respostas (0-1)
        max_tokens: Tamanho máximo da resposta
        
    Returns:
        Instância do ChatOpenAI configurada
    """
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=st.secrets["openai"]["api_key"],
        streaming=True
    )

def _create_chain(
    prompt_template: str,
    llm: Optional[ChatOpenAI] = None,
    context: Optional[str] = None
):
    """Cria uma chain de processamento de texto completa.
    
    Args:
        prompt_template: Template do prompt com {texto} como placeholder
        llm: Modelo de linguagem (opcional)
        context: Contexto adicional para o prompt (opcional)
        
    Returns:
        Chain pronta para invocação
    """
    llm = llm or get_llm()
    
    # Adiciona contexto se fornecido
    if context:
        prompt_template = f"CONTEXTO:\n{context}\n\n{prompt_template}"
    
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    return (
        {"texto": RunnablePassthrough()}  # Recebe o texto de input
        | prompt                          # Aplica o template
        | llm                            # Processa com o LLM
        | StrOutputParser()              # Converte para string
    )

def gerar_resumo_projeto(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Gera um resumo executivo profissional do projeto.
    
    Args:
        texto_projeto: Texto contendo detalhes do projeto
        context: Informações adicionais (opcional)
        llm: Modelo customizado (opcional)
        
    Returns:
        Resumo formatado em markdown ou string vazia em caso de erro
    """
    template = """
    Gere um resumo executivo profissional (150-200 palavras) contendo:
    
    ## Objetivos
    - Principais metas e propósitos
    
    ## Público-Alvo
    - Quem será beneficiado
    
    ## Metodologia
    - Abordagem principal
    
    ## Impacto Esperado
    - Resultados culturais previstos
    
    Use linguagem clara e markdown para formatação.
    
    PROJETO:
    {texto}"""
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar resumo: {str(e)}")
        return ""

def gerar_orcamento(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Gera orçamento detalhado em formato tabular."""
    template = """
    Gere um orçamento detalhado com:
    
    | Categoria         | Item               | Quantidade | Valor Unitário | Total       |
    |-------------------|--------------------|------------|----------------|-------------|
    | Materiais         | [itens]            | [qtd]      | R$ [valor]     | R$ [total]  |
    | Pessoal           | [cargos]           | [horas]    | R$ [hora]      | R$ [total]  |
    | Infraestrutura    | [recursos]         | [período]  | R$ [valor]     | R$ [total]  |
    | Outros            | [despesas]         | -          | -              | R$ [total]  |
    
    PROJETO:
    {texto}"""
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar orçamento: {str(e)}")
        return ""

def gerar_cronograma(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Gera cronograma com marcos temporais."""
    template = """
    Crie um cronograma detalhado com:
    
    ### Fase 1: Planejamento
    - [ ] Tarefa 1 (DD/MM - DD/MM)
    - [ ] Tarefa 2 (DD/MM - DD/MM)
    
    ### Fase 2: Execução
    - [ ] Tarefa 3 (DD/MM - DD/MM)
    - [ ] Marco Principal (DD/MM)
    
    ### Fase 3: Finalização
    - [ ] Entrega Final (DD/MM)
    
    PROJETO:
    {texto}"""
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar cronograma: {str(e)}")
        return ""

def gerar_objetivos(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Formula objetivos no padrão SMART."""
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
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar objetivos: {str(e)}")
        return ""

def gerar_justificativa(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Elabora justificativa técnica."""
    template = """
    Desenvolva uma justificativa com:
    1. CONTEXTO CULTURAL (por que é importante?)
    2. INOVAÇÃO (o que traz de novo?)
    3. IMPACTO SOCIAL (benefícios para quem?)
    4. VIABILIDADE (por que pode dar certo?)
    
    USE PARÁGRAFOS COESOS E ARGUMENTATIVOS
    
    PROJETO:
    {texto}"""
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar justificativa: {str(e)}")
        return ""

def gerar_etapas_trabalho(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Detalha etapas de execução."""
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
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar etapas: {str(e)}")
        return ""

def gerar_ficha_tecnica(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> str:
    """Produz ficha técnica completa."""
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
    
    try:
        chain = _create_chain(template, llm, context)
        return chain.invoke(texto_projeto[:15000])
    except Exception as e:
        st.error(f"Falha ao gerar ficha técnica: {str(e)}")
        return ""

def gerar_documento_completo(
    texto_projeto: str,
    context: Optional[str] = None,
    llm: Optional[ChatOpenAI] = None
) -> Dict[str, str]:
    """Gera todos os documentos de uma vez.
    
    Returns:
        Dicionário com todos os documentos gerados
    """
    return {
        "resumo": gerar_resumo_projeto(texto_projeto, context, llm),
        "orcamento": gerar_orcamento(texto_projeto, context, llm),
        "cronograma": gerar_cronograma(texto_projeto, context, llm),
        "objetivos": gerar_objetivos(texto_projeto, context, llm),
        "justificativa": gerar_justificativa(texto_projeto, context, llm),
        "etapas": gerar_etapas_trabalho(texto_projeto, context, llm),
        "ficha_tecnica": gerar_ficha_tecnica(texto_projeto, context, llm)
    }