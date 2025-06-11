from langchain_core.tools import tool
from RAG_job_posts_engine.rag_pipeline import query_job_posts


# Define tools for the retrieval agent
@tool
def search_jobs(query: str) -> str:
    """Search for job listings based on provided criteria such as role, location, experience level, etc."""
    # Mock response - in a real system, this would connect to job listing APIs
    return query_job_posts()