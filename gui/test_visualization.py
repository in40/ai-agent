import sys
import os
from pathlib import Path
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

# Test if we can import and visualize the graph
from langgraph_agent.langgraph_agent import create_enhanced_agent_graph

print("Creating graph...")
graph = create_enhanced_agent_graph()
print("Getting graph...")
g = graph.get_graph()

print("Available methods:")
methods = [method for method in dir(g) if 'draw' in method.lower() or 'print' in method.lower()]
print(methods)

print("\nDrawing mermaid diagram...")
mermaid_code = g.draw_mermaid()
print(mermaid_code[:500] + "..." if len(mermaid_code) > 500 else mermaid_code)