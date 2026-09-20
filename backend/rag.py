from langchain_classic.agents import AgentExecutor, create_openai_tools_agent
from langchain_community.agent_toolkits import SQLDatabaseToolkit
# --- LangChain & SQL Toolkit Imports ---
from langchain_community.utilities import SQLDatabase

# from langchain.agents import AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from llm import get_llm
from app.vector_store import get_vector_store

rag_retriever = get_vector_store().as_retriever(search_kwargs={"k": 3})

# B. SQL Database & Toolkit Setup
from app.config import settings

sql_db = SQLDatabase.from_uri(settings.NEON_SQLALCHEMY_URI)
sql_toolkit = SQLDatabaseToolkit(db=sql_db, llm=get_llm())
sql_tools = sql_toolkit.get_tools()

sql_prompt_template = ChatPromptTemplate.from_messages([
    ("system", "You are an expert SQL agent. Access available tables: vendors, audit_logs, retention_records, compliance_reviews."),
    ("user", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

sql_agent_runnable = create_openai_tools_agent(get_llm(), sql_tools, sql_prompt_template)
sql_executor = AgentExecutor(agent=sql_agent_runnable, tools=sql_tools, verbose=False)

# Helper function to execute semantic RAG
def execute_rag_retrieval(query: str) -> tuple[str, list[dict]]:
    nodes = rag_retriever.invoke(query)
    formatted = []
    sources = []
    for node in nodes:
        metadata = node.metadata or {}
        source = metadata.get("source") or metadata.get("file_name") or "Policy Document"
        content = node.page_content
        formatted.append(f"[Source: {source}]:\n{content}")
        sources.append({
            "source": source,
            "page": metadata.get("page"),
            "snippet": content[:200],
        })
    context = "\n\n---\n\n".join(formatted) if formatted else "No relevant policy documents found."
    return context, sources

# Helper function to execute SQL
def execute_sql_query(query: str) -> str:
    res = sql_executor.invoke({"input": query})
    return res.get("output", "No database results returned.")
