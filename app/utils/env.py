import os
from typing import Optional
from app.core.logging import get_logger

logger = get_logger("app.utils.env")

def check_env_variables(required_vars: list[str]) -> bool:
    """
    Check if all required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        True if all required variables are set, False otherwise
    """
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.critical(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.critical("Make sure the .env file exists and contains the required variables.")
        return False
    
    return True


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get an environment variable with better logging.
    
    Args:
        name: Name of the environment variable
        default: Default value if the variable is not set
        
    Returns:
        The value of the environment variable or the default value
    """
    value = os.getenv(name, default)
    if value is None:
        logger.warning(f"Environment variable {name} not set")
    return value