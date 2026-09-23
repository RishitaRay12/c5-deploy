import os
# from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI

from app.config import settings


def get_llm():


    # Complex tasks use Groq/OpenAI configuration
    provider = settings.LLM_PROVIDER

    if provider == "groq":

        if not settings.GROQ_API_KEY:
            raise RuntimeError(
                "GROQ_API_KEY is not configured."
            )

        return ChatOpenAI(
            model=settings.GROQ_MODEL,
            api_key=settings.GROQ_API_KEY,
            base_url=settings.GROQ_BASE_URL,
            temperature=0.2,
        )

    if provider == "openai":

        if not settings.OPENAI_API_KEY:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        return ChatOpenAI(
            model=settings.OPENAI_MODEL,
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_BASE_URL,
            temperature=0.2,
        )

    if provider == "ollama":

        return ChatOllama(
            model=settings.OLLAMA_MODEL,
            base_url=settings.OLLAMA_BASE_URL,
            temperature=0.2,
        )

    raise ValueError(
        f"Unsupported LLM_PROVIDER: {provider}"
    )

# class LLM_Service:
#    def __init__(self):
#         model = os.getenv("LLM_MODEL")
#         api_key = os.getenv("LLM_KEY")
#         url = os.getenv("BASIC_URL")

#         self.llm = ChatOpenAI(model=model, api_key=api_key, base_url=url)


# A. LlamaIndex Semantic Splitter RAG Setup
def setup_semantic_rag():
    from app.vector_store import get_vector_store

    return get_vector_store().as_retriever(search_kwargs={"k": 3})

