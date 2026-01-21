# LangGraph Studio Integration Guide

This document outlines how to integrate the LangGraph visual editor with LangGraph Studio.

## About LangGraph Studio

LangGraph Studio is a visual development environment for LangGraph applications that provides:
- Visual graph editing capabilities
- Real-time execution monitoring
- Step-through debugging
- State visualization
- Human-in-the-loop capabilities

## Integration Approaches

### 1. Direct Integration Method

LangGraph Studio can be integrated directly with your existing LangGraph workflows:

```python
from langgraph.studio import ApplicationBuilder

# Assuming you have your existing workflow defined
from langgraph_agent.langgraph_agent import create_enhanced_agent_graph

# Create your graph
graph = create_enhanced_agent_graph()

# Create a LangGraph Studio application
builder = ApplicationBuilder()
app = builder \
    .with_graph(graph) \
    .with_config({"thread_id": "example-thread"}) \
    .build()

# Run the application
if __name__ == "__main__":
    app.launch()
```

### 2. Configuration File Method

Create a `langgraph.json` configuration file to define your agent:

```json
{
  "graph": "./path/to/your/graph.py:create_enhanced_agent_graph",
  "entry_point": "get_schema",
  "state_schema": "./path/to/your/state.py:AgentState",
  "environment": {
    "OPENAI_API_KEY": "...",
    "OTHER_CONFIG_VALUES": "..."
  }
}
```

Then run LangGraph Studio:
```bash
langgraph dev
```

### 3. Web API Integration

For integration with the existing Streamlit and React applications, you can create an API endpoint that connects to LangGraph Studio:

```python
# api/integration.py
from fastapi import FastAPI
from langgraph.studio import RemoteApplication
import uvicorn

app = FastAPI()

@app.get("/studio-integration")
async def get_studio_integration():
    # Connect to a running LangGraph Studio instance
    # This would require LangGraph Studio to be running separately
    remote_app = RemoteApplication(url="http://localhost:8080")
    
    # Get graph information
    graph_info = await remote_app.get_graph()
    
    return {"graph": graph_info, "status": "connected"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## Benefits of Integration

1. **Advanced Visualization**: Leverage LangGraph Studio's sophisticated visualization tools
2. **Professional Debugging**: Access to enterprise-grade debugging features
3. **Team Collaboration**: Shared environments for team development
4. **Cloud Deployment**: Easy deployment options to cloud platforms
5. **Version Control**: Built-in versioning for graph workflows

## Implementation Steps

1. Install LangGraph Studio:
   ```bash
   pip install langgraph-studio
   ```

2. Configure your existing graph for Studio compatibility:
   - Ensure your graph follows LangGraph best practices
   - Define clear state schemas
   - Implement proper error handling

3. Create a launch script:
   ```python
   # studio_launcher.py
   from langgraph.studio import ApplicationBuilder
   from langgraph_agent.langgraph_agent import create_enhanced_agent_graph
   
   def launch_studio():
       graph = create_enhanced_agent_graph()
       
       app_builder = ApplicationBuilder()
       app = app_builder \
           .with_graph(graph) \
           .with_entry_point("__start__") \
           .build()
       
       # Launch the studio interface
       app.launch(host="localhost", port=8080)
   
   if __name__ == "__main__":
       launch_studio()
   ```

4. Run LangGraph Studio alongside your existing applications

## Considerations

- LangGraph Studio requires specific hardware (currently only supports Apple Silicon Macs)
- Your existing visualization tools can coexist with Studio
- Consider using Studio for development and your custom tools for deployment
- The integration may require adapting your current state management approach