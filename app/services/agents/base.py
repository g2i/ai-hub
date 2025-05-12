from app.core.logging import get_logger

logger = get_logger("app.services.agents")

class AgentBase:
    """Base class for AI agents."""
    
    def __init__(self, config=None):
        """
        Initialize the agent.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        logger.info(f"Initializing {self.__class__.__name__} agent")
    
    async def process(self, input_data):
        """
        Process input data with the agent.
        
        This method should be implemented by subclasses.
        
        Args:
            input_data: The data to process
            
        Returns:
            The processed result
        """
        raise NotImplementedError("Subclasses must implement process()")