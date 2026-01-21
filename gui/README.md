# LangGraph Visual Editor

This is a web-based GUI application for visualizing and interacting with the LangGraph workflow used in the AI agent.

## Features

- **Visualization**: View the workflow graph with nodes and edges
- **Details**: Explore the nodes, edges, and conditional logic of the workflow
- **Simulation**: Run the workflow with sample inputs and different configurations
- **Export/Import**: Save and load workflow definitions

## How to Run

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```

3. Access the application in your browser at `http://localhost:8501`

## Tabs Overview

1. **Visualization**: Shows the workflow as a directed graph
2. **Workflow Details**: Lists all nodes and edges in the workflow
3. **Run Simulation**: Allows you to run the workflow with custom inputs
4. **Export/Import**: Enables saving/loading workflow definitions

## Technical Details

The application leverages LangGraph's built-in visualization capabilities to render the workflow graph. It uses Streamlit for the web interface and allows interaction with the underlying LangGraph workflow.

## Dependencies

- streamlit
- langchain
- langgraph
- graphviz
- grandalf