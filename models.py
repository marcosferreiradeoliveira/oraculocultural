from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain_core.output_parsers import StrOutputParser
import streamlit as st

# Configuração centralizada do LLM com cache e usando secrets
@st.cache_resource
def get_llm(model="gpt-4-turbo", temperature=0.7, max_tokens=2000):
    """Retorna uma instância configurada e em cache do LLM"""
    return ChatOpenAI(
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        openai_api_key=st.secrets["openai"]["api_key"]  # Acesso seguro à chave
    )

# Função base para criar chains com tratamento de texto
def _create_chain(prompt_template, llm=None, diagnostico=None):
    """Cria chain com tratamento consistente de input"""
    if not llm:
        llm = get_llm()
    
    instrucoes = f"\nConsidere o seguinte diagnóstico:\n{diagnostico}\n" if diagnostico else ""
    full_template = instrucoes + prompt_template
    
    prompt = ChatPromptTemplate.from_template(full_template)
    return LLMChain(llm=llm, prompt=prompt, output_parser=StrOutputParser())

def gerar_resumo_projeto(texto_projeto, diagnostico=None, llm=None):
    """Gera resumo conciso do projeto (150-200 palavras)"""
    prompt_template = """
    Gere um resumo profissional do seguinte projeto, destacando:
    - Objetivos principais
    - Público-alvo
    - Metodologia
    - Impacto cultural
    
    Use linguagem clara e objetiva.
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})  # Limita o tamanho do texto

def gerar_orcamento(texto_projeto, diagnostico=None, llm=None):
    """Gera orçamento detalhado dividido em categorias"""
    prompt_template = """
    Gere um orçamento detalhado para o projeto abaixo, incluindo:
    - Materiais e suprimentos (itens e valores)
    - Honorários profissionais (funções e valores)
    - Infraestrutura e logística (itens e valores)
    - Outras despesas relevantes
    - Total estimado com valores consolidados
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})

def gerar_cronograma(texto_projeto, diagnostico=None, llm=None):
    """Gera cronograma com fases e prazos estimados"""
    prompt_template = """
    Crie um cronograma detalhado com base nas fases:
    1. Planejamento (atividades e duração)
    2. Execução (etapas e marcos temporais)
    3. Finalização (entregas finais)
    4. Avaliação (métodos e período)
    
    Indique prazos realistas para cada etapa.
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})

def gerar_objetivos(texto_projeto, diagnostico=None, llm=None):
    """Reformula objetivos no formato SMART"""
    prompt_template = """
    Reformule os objetivos do projeto no formato SMART:
    - Específicos (claros e bem definidos)
    - Mensuráveis (com indicadores quantificáveis)
    - Atingíveis (realistas com os recursos)
    - Relevantes (alinhados ao propósito)
    - Temporais (com prazos definidos)
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})

def gerar_justificativa(texto_projeto, diagnostico=None, llm=None):
    """Gera justificativa técnica convincente"""
    prompt_template = """
    Elabore uma justificativa técnica que inclua:
    1. Contexto e motivações do projeto
    2. Contribuições culturais esperadas
    3. Relevância social e técnica
    4. Benefícios para o público-alvo
    5. Alinhamento com políticas culturais
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})

def gerar_etapas_trabalho(texto_projeto, diagnostico=None, llm=None):
    """Detalha etapas do projeto"""
    prompt_template = """
    Descreva detalhadamente as etapas de trabalho:
    [Planejamento]
    - Atividades específicas
    - Responsáveis
    - Recursos necessários
    
    [Execução]
    - Fases operacionais
    - Marcos importantes
    - Métodos de acompanhamento
    
    [Monitoramento]
    - Indicadores de desempenho
    - Ferramentas de avaliação
    
    [Encerramento]
    - Entregas finais
    - Relatórios obrigatórios
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})

def gerar_ficha_tecnica(texto_projeto, diagnostico=None, llm=None):
    """Gera ficha técnica completa"""
    prompt_template = """
    Crie uma ficha técnica profissional contendo:
    [Equipe]
    - Funções/chave
    - Responsabilidades específicas
    - Qualificações requeridas
    - Tipo de vínculo (CLT, PJ, voluntário)
    
    [Recursos]
    - Equipamentos necessários
    - Espaços físicos requeridos
    - Materiais de consumo
    
    Projeto: {texto}"""
    
    chain = _create_chain(prompt_template, llm, diagnostico)
    return chain.run({"texto": texto_projeto[:10000]})