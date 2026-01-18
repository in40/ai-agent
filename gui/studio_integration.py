#!/usr/bin/env python3
"""
LangGraph Studio Integration Launcher

This script provides integration with LangGraph Studio for enhanced visualization
and debugging capabilities.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def check_langgraph_studio():
    """Check if LangGraph Studio is available in the environment."""
    try:
        import langgraph_studio
        return True
    except ImportError:
        return False

def launch_studio_integration():
    """Launch LangGraph Studio with the current workflow."""
    if not check_langgraph_studio():
        print("LangGraph Studio is not installed.")
        print("To install: pip install langgraph-studio")
        print("Note: LangGraph Studio currently requires Apple Silicon Macs.")
        return
    
    try:
        from langgraph.studio import ApplicationBuilder
        from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
        
        # Create the graph
        graph = create_enhanced_agent_graph()
        
        # Create and launch the application
        builder = ApplicationBuilder()
        app = builder \
            .with_graph(graph) \
            .with_entry_point("__start__") \
            .build()
        
        print("Launching LangGraph Studio integration...")
        print("Access the studio at: http://localhost:8080")
        print("Press Ctrl+C to stop the server.")
        
        app.launch(host="localhost", port=8080)
        
    except Exception as e:
        print(f"Error launching LangGraph Studio integration: {e}")
        import traceback
        traceback.print_exc()

def create_studio_config():
    """Create a configuration file for LangGraph Studio."""
    config_content = {
        "graph": "langgraph_agent.langgraph_agent:create_enhanced_agent_graph",
        "entry_point": "__start__",
        "environment": {
            "OPENAI_API_KEY": "${OPENAI_API_KEY}",
            "ANTHROPIC_API_KEY": "${ANTHROPIC_API_KEY}",
            "USE_SECURITY_LLM": "${USE_SECURITY_LLM:true}",
            "TERMINATE_ON_POTENTIALLY_HARMFUL_SQL": "${TERMINATE_ON_POTENTIALLY_HARMFUL_SQL:true}"
        }
    }
    
    import json
    with open("langgraph_studio_config.json", "w") as f:
        json.dump(config_content, f, indent=2)
    
    print("Created LangGraph Studio configuration file: langgraph_studio_config.json")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "config":
            create_studio_config()
        else:
            print("Usage: python studio_integration.py [config]")
    else:
        launch_studio_integration()