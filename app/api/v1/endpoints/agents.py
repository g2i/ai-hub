from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("")
async def list_agents():
    """
    List available AI agents.
    
    Returns:
        List of available agent types and their capabilities.
    """
    # Placeholder for future implementation
    return {"message": "Agent listing functionality coming soon"}

@router.get("/info")
async def agents_info():
    """
    Get information about AI agent capabilities.
    
    Returns:
        Detailed information about agent capabilities and configurations.
    """
    # Placeholder for future implementation
    return {
        "message": "Agent information functionality coming soon",
        "version": "v1"
    }