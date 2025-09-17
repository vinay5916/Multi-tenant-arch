"""
Aviation Agents Module for Google ADK
"""

# Import the main agent for ADK discovery
try:
    from .aviation_agent import root_agent, AviationBaseAgent
    
    # Export for ADK
    __all__ = ["root_agent", "AviationBaseAgent"]
    
except ImportError as e:
    print(f"Warning: Could not import aviation agent: {e}")
    root_agent = None