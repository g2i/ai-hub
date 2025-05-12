from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class AgentRequest(BaseModel):
    """Base model for agent requests."""
    input: str = Field(..., description="The input text to process")
    options: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Optional configuration parameters for the agent"
    )


class AgentResponse(BaseModel):
    """Base model for agent responses."""
    output: str = Field(..., description="The output text from the agent")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, 
        description="Additional metadata about the processing"
    )