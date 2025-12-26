"""
Health check endpoint
"""
from fastapi import APIRouter, Request
import os
import httpx

router = APIRouter()


@router.get("/health")
async def health_check(request: Request):
    """Health check endpoint"""
    duckdb_conn = request.app.state.duckdb
    
    # Test DuckDB connection
    try:
        result = duckdb_conn.execute("SELECT 1").fetchone()
        duckdb_status = "healthy" if result else "unhealthy"
    except Exception as e:
        duckdb_status = f"error: {str(e)}"
    
    # Test Ollama connection
    ollama_status = "unknown"
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            # Try to list models first (lighter check)
            try:
                resp = await client.get(f"{ollama_url}/api/tags")
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    model_names = [m.get("name", "") for m in models]
                    if any(ollama_model in name for name in model_names):
                        ollama_status = f"healthy (model '{ollama_model}' available)"
                    else:
                        ollama_status = f"connected but model '{ollama_model}' not found. Available: {', '.join(model_names[:3])}"
                else:
                    ollama_status = f"error: HTTP {resp.status_code}"
            except Exception as e:
                ollama_status = f"error: {str(e)}"
    except httpx.ConnectError:
        ollama_status = f"unreachable at {ollama_url} (is Ollama running?)"
    except httpx.TimeoutException:
        ollama_status = f"timeout connecting to {ollama_url}"
    except Exception as e:
        ollama_status = f"error: {str(e)}"
    
    return {
        "status": "ok",
        "duckdb": duckdb_status,
        "ollama": ollama_status,
        "ollama_url": ollama_url,
        "ollama_model": ollama_model,
        "timestamp": __import__("time").time()
    }


@router.get("/health/ollama")
async def ollama_health_check():
    """Detailed Ollama health check"""
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "llama3")
    
    result = {
        "url": ollama_url,
        "model": ollama_model,
        "reachable": False,
        "models_available": [],
        "model_found": False,
        "error": None
    }
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Check if Ollama is reachable
            try:
                resp = await client.get(f"{ollama_url}/api/tags")
                if resp.status_code == 200:
                    result["reachable"] = True
                    models_data = resp.json().get("models", [])
                    result["models_available"] = [m.get("name", "") for m in models_data]
                    result["model_found"] = any(ollama_model in name for name in result["models_available"])
                else:
                    result["error"] = f"HTTP {resp.status_code}: {resp.text}"
            except httpx.ConnectError:
                result["error"] = f"Cannot connect to {ollama_url}. Is Ollama running? Try: `ollama serve`"
            except httpx.TimeoutException:
                result["error"] = f"Timeout connecting to {ollama_url}"
            except Exception as e:
                result["error"] = str(e)
    except Exception as e:
        result["error"] = str(e)
    
    return result

