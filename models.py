from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from langchain.memory import ConversationBufferMemory

def get_llm():
    """Retorna uma instância configurada do LLM"""
    return ChatOpenAI(
        model="gpt-4-turbo",
        temperature=0.7,
        max_tokens=2000
    )


def carrega_modelo(tipo_arquivo, conteudo):
    """
    Carrega e configura o modelo LLM com base no tipo de arquivo e conteúdo
    
    Parâmetros:
    - tipo_arquivo: Tipo do arquivo ('Pdf', 'Csv', etc.)
    - conteudo: Conteúdo extraído do arquivo
    
    Retorna: Modelo LLM configurado
    """
    llm = ChatOpenAI(model="gpt-4-turbo", temperature=0.7)

    prompt = ChatPromptTemplate.from_template(
        f"""Você é um assistente especializado em análise de projetos culturais.
        Estou enviando um arquivo do tipo {tipo_arquivo} com o seguinte conteúdo:
        
        {conteudo}
        
        Por favor, analise e forneça feedback detalhado.
        """
    )

    memory = ConversationBufferMemory()
    memory.save_context({"input": conteudo}, {"output": ""})

    return llm, prompt, memory


def gerar_resumo_projeto(llm, texto_projeto):
    """Gera um resumo conciso do projeto usando o modelo LLM"""
    
    # Limitando o texto a 10.000 caracteres para evitar custos altos
    texto_limitado = texto_projeto[:10000]
    
    prompt_resumo = ChatPromptTemplate.from_template(
        """Você é um especialista em análise de projetos culturais. 
        Gere um resumo conciso (150-200 palavras) do seguinte projeto:
        
        {texto}
        
        Destaque:
        - Objetivos principais
        - Público-alvo
        - Metodologia
        - Impacto cultural
        
        Use linguagem clara e objetiva. Resumo:"""
    )
    
    # Configurando a cadeia de execução
    chain = LLMChain(prompt=prompt_resumo, llm=llm)
    
    # Invocando a cadeia para gerar o resumo
    return chain.run({"texto": texto_limitado})

def gerar_orcamento(llm, texto_projeto):
    """Gera um orçamento básico do projeto com base no texto do projeto usando o modelo LLM"""
    
    # Prompt do orçamento
    prompt_orcamento = ChatPromptTemplate.from_template(
        """Você é um especialista em projetos culturais. 
        Gere um orçamento detalhado para o projeto a seguir, considerando as principais despesas e fontes de financiamento:

        {texto}
        
        O orçamento deve ser dividido nas seguintes categorias:
        - Materiais e suprimentos
        - Honorários dos profissionais
        - Infraestrutura e logística
        - Outras despesas (como transporte, alimentação, etc.)
        Total: (valor total estimado)
        """
    )

    # Configurando a cadeia de execução
    chain = LLMChain(prompt=prompt_orcamento, llm=llm)
    
    # Invocando a cadeia para gerar o orçamento
    return chain.run({"texto": texto_projeto})

def gerar_cronograma(llm, texto_projeto):
    """Gera um cronograma do projeto com base no texto do projeto usando o modelo LLM"""
    
    # Prompt do cronograma
    prompt_cronograma = ChatPromptTemplate.from_template(
        """Você é um especialista em gestão de projetos culturais. 
        Gere um cronograma detalhado para o projeto a seguir, com base nas principais etapas do projeto. 
        O cronograma deve ser dividido nas seguintes fases e incluir um período estimado para cada uma:

        {texto}
        
        As fases devem incluir:
        - Planejamento
        - Execução
        - Finalização e Avaliação
        """
    )

    # Configurando a cadeia de execução
    chain = LLMChain(prompt=prompt_cronograma, llm=llm)
    
    # Invocando a cadeia para gerar o cronograma
    return chain.run({"texto": texto_projeto})

def gerar_objetivos(llm, texto_projeto):
    """Gera objetivos SMART para o projeto com base no texto do projeto usando o modelo LLM"""
    
    # Prompt de objetivos SMART
    prompt_objetivos = ChatPromptTemplate.from_template(
        """Você é um especialista em gestão de projetos culturais. 
        Gere objetivos SMART para o projeto a seguir. Cada objetivo deve ser específico, mensurável, alcançável, relevante e com prazo determinado.

        {texto}
        
        Exemplo de formato para cada objetivo:
        - Objetivo 1: Descrição do objetivo
        - Objetivo 2: Descrição do objetivo
        """
    )

    # Configurando a cadeia de execução
    chain = LLMChain(prompt=prompt_objetivos, llm=llm)
    
    # Invocando a cadeia para gerar os objetivos SMART
    return chain.run({"texto": texto_projeto})

def gerar_justificativa(llm, texto_projeto):
    """Gera uma justificativa técnica para o projeto com base no texto do projeto usando o modelo LLM"""
    
    # Prompt de justificativa técnica
    prompt_justificativa = ChatPromptTemplate.from_template(
        """Você é um especialista em projetos culturais. 
        Gere uma justificativa técnica clara e convincente para o projeto a seguir. A justificativa deve explicar os motivos e objetivos do projeto, suas contribuições para a cultura, sociedade ou área específica, e por que é importante realizar esse projeto.

        {texto}
        """
    )

    # Configurando a cadeia de execução
    chain = LLMChain(prompt=prompt_justificativa, llm=llm)
    
    # Invocando a cadeia para gerar a justificativa técnica
    return chain.run({"texto": texto_projeto})
