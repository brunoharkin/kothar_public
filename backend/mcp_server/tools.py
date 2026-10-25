import uuid
from typing import Optional

from backend.memory.semantic.chroma_client import chroma_memory
from backend.mcp_server.trace_interceptor import trace_mcp_event, get_or_create_session

session_id = get_or_create_session()

async def search_memory(query: str, category: Optional[str] = None, threshold: float = 0.6) -> str:
    """
    Search the RAG semantic memory (ChromaDB) for relevant knowledge, skills, or context.
    
    Args:
        query: The search query string.
        category: Optional category filter.
        threshold: The similarity threshold (0.0 to 1.0).
    """
    try:
        results = await chroma_memory.search_skills(
            query=query,
            n_results=5,
            category=category,
            threshold=threshold
        )
        
        # Log to trace system
        trace_mcp_event(
            session_id=session_id,
            tool_name="Memory:Search",
            input_data={"query": query, "category": category, "threshold": threshold},
            output_data={"found": len(results), "results": results}
        )
        
        if not results:
            return "No relevant memories found."
            
        formatted_results = []
        for r in results:
            meta = r.get("metadata", {})
            doc = r.get("document", "")
            sim = r.get("similarity", 0)
            formatted_results.append(f"--- MATCH ({sim * 100:.1f}%) ---\nName: {meta.get('name')}\n{doc}\n")
            
        return "\n".join(formatted_results)
    except Exception as e:
        trace_mcp_event(session_id, "Memory:Search", {"query": query}, str(e), is_error=True, error_msg=str(e))
        return f"Error searching memory: {str(e)}"

async def save_memory(name: str, description: str, content: str, tags: str = "") -> str:
    """
    Save new knowledge or context into the RAG semantic memory (ChromaDB).
    
    Args:
        name: Short name or title of the memory.
        description: Brief explanation of what this memory contains.
        content: The full markdown or text content to store.
        tags: Comma-separated list of tags.
    """
    skill_id = str(uuid.uuid4())
    tag_list = [t.strip() for t in tags.split(",") if t.strip()]
    
    try:
        await chroma_memory.upsert_skill(
            skill_id=skill_id,
            name=name,
            description=description,
            yaml_content=content,
            category="mcp_knowledge",
            tags=tag_list
        )
        
        result_msg = f"Successfully saved memory '{name}' with ID {skill_id}."
        
        trace_mcp_event(
            session_id=session_id,
            tool_name="Memory:Save",
            input_data={"name": name, "description": description, "tags": tag_list},
            output_data={"result": result_msg, "id": skill_id}
        )
        
        return result_msg
    except Exception as e:
        trace_mcp_event(session_id, "Memory:Save", {"name": name}, str(e), is_error=True, error_msg=str(e))
        return f"Error saving memory: {str(e)}"

async def register_tools(mcp):
    """Register tools with the FastMCP instance."""
    mcp.tool()(search_memory)
    mcp.tool()(save_memory)
