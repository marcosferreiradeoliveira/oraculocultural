from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain

def get_llm():
    """Retorna uma instância configurada do LLM"""
    return ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2000
    )

def gerar_resumo_projeto(llm, texto_projeto, diagnostico=None):
    texto_limitado = texto_projeto[:10000]
    instrucoes = f"""
    Considere o seguinte diagnóstico ao gerar o resumo:

    {diagnostico}

    Adapte o conteúdo conforme necessário.
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Gere um resumo conciso (150-200 palavras) do seguinte projeto, destacando:
        - Objetivos principais
        - Público-alvo
        - Metodologia
        - Impacto cultural

        Use linguagem clara e objetiva. Resumo:"""
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_limitado})

def gerar_orcamento(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao elaborar o orçamento:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Gere um orçamento detalhado para o projeto abaixo, dividido em:
        - Materiais e suprimentos
        - Honorários dos profissionais
        - Infraestrutura e logística
        - Outras despesas
        - Total estimado

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})

def gerar_cronograma(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao gerar o cronograma:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Crie um cronograma detalhado com base nas fases:
        - Planejamento
        - Execução
        - Finalização e Avaliação

        Indique o tempo previsto para cada etapa.

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})

def gerar_objetivos(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao formular os objetivos SMART:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Reformule os objetivos do projeto no formato SMART:
        - Específicos
        - Mensuráveis
        - Atingíveis
        - Relevantes
        - Temporais

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})

def gerar_justificativa(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao redigir a justificativa:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Gere uma justificativa técnica clara e convincente para o projeto, abordando:
        - Motivações
        - Contribuições culturais
        - Relevância social e técnica

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})

def gerar_etapas_trabalho(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao organizar as etapas:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Descreva as etapas do projeto, organizadas em:
        - Planejamento
        - Execução
        - Monitoramento
        - Encerramento

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})

def gerar_ficha_tecnica(llm, texto_projeto, diagnostico=None):
    instrucoes = f"""
    Considere o seguinte diagnóstico ao montar a ficha técnica:

    {diagnostico}
    """ if diagnostico else ""

    prompt = ChatPromptTemplate.from_template(
        f"""{instrucoes}

        Gere a ficha técnica do projeto com:
        - Nome das funções
        - Atuação/responsabilidade
        - Tipo de vínculo (contrato, parceiro, interno)

        Projeto:
        {{texto}}
        """
    )

    chain = LLMChain(prompt=prompt, llm=llm)
    return chain.run({"texto": texto_projeto})
