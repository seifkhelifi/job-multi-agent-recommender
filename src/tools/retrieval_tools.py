from langchain_core.tools import tool
import requests

# Define FastAPI endpoint
API_URL = (
    "http://localhost:8000/query"  # adjust host/port from your FastAPI server config
)


@tool
def search_jobs(query: str) -> str:
    """Search for job listings based on provided criteria such as role, location, experience level, etc."""
    try:
        response = requests.post(API_URL, json={"query": query}, timeout=30)
        response.raise_for_status()
        return response.json().get("response", "No response from API")
    except Exception as e:
        return f"Error while querying job API: {str(e)}"
