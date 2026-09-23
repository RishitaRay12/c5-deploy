from langchain.messages import HumanMessage, AIMessage, SystemMessage
from schema import AgentState
from llm import get_llm


def direct_chat_node(state: AgentState) -> dict:
    """Answers simple conversational queries directly without evaluation or RAG."""
    query = state.get("query", "")
    
    system_prompt = (
        "You are a helpful Retail Policy Assistant. Answer casual greetings and identity "
        "questions politely and concisely."
    )
    
    response = get_llm().invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=query)
    ])
    
    answer = response.content
    usage = (
        (response.response_metadata or {}).get("token_usage")
        or getattr(response, "usage_metadata", None)
        or {}
    )
    # ✅ SAFE: (usage.get("prompt_tokens_details") or {}) handles both missing keys AND None values
    prompt_details = usage.get("prompt_tokens_details") or {}
    cached_tokens = prompt_details.get("cached_tokens", 0)
    prompt_tokens = usage.get("prompt_tokens", usage.get("input_tokens"))
    completion_tokens = usage.get("completion_tokens", usage.get("output_tokens"))
    total_tokens = usage.get("total_tokens")
    if total_tokens is None and prompt_tokens is not None and completion_tokens is not None:
        total_tokens = prompt_tokens + completion_tokens
    token_info = {
                    "usage": {
                        "prompt_tokens": prompt_tokens,
                        "completion_tokens": completion_tokens,
                        "total_tokens": total_tokens,
                        "prompt_tokens_details": {
                            "cached_tokens": cached_tokens
                        }
                    },
    
                    "cache_status": "HIT" if cached_tokens > 0 else "MISS"
                }
    return {
        "final_response": answer,
        "messages": [AIMessage(content=answer)],
        "human_handoff": False,
        "relevance_score": 1.0,
        "faithfulness_score": 1.0,
        "confidence_score": 1.0,
        "token_usage": token_info
    }