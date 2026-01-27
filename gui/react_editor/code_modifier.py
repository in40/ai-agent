"""
Code modification engine for applying changes from the React UI directly to LangGraph code.
Uses Python's AST module to safely parse, modify, and write back to Python files.
"""
import ast
import astor  # For converting AST back to code with formatting
import json
import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional


class BackupManager:
    """Manages file backups before modifications."""
    
    def __init__(self, backup_dir: str = "./backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, file_path: str) -> str:
        """Create a backup of the file and return the backup path."""
        import time
        file_path = Path(file_path)
        timestamp = str(int(time.time()))
        backup_path = self.backup_dir / f"{file_path.name}.{timestamp}.bak"
        shutil.copy2(file_path, backup_path)
        return str(backup_path)
    
    def restore_from_backup(self, original_path: str, backup_path: str):
        """Restore the original file from backup."""
        shutil.copy2(backup_path, original_path)


class NodeFunctionUpdater(ast.NodeTransformer):
    """Handles updating node functions based on UI configuration."""
    
    def __init__(self, node_configs: List[Dict]):
        self.node_configs = {config['nodeFunction']: config for config in node_configs if config.get('nodeFunction')}
    
    def visit_FunctionDef(self, node):
        """Update existing node functions or add new ones."""
        # Check if this is a node function that needs updating
        if node.name.endswith('_node') and node.name in self.node_configs:
            config = self.node_configs[node.name]
            
            # Update the function body based on configuration
            new_body = self._create_function_body(config)
            node.body = new_body
        
        return self.generic_visit(node)
    
    def _create_function_body(self, config: Dict) -> List[ast.stmt]:
        """Create a function body based on the configuration."""
        # Create a docstring
        docstring = ast.Expr(value=ast.Constant(value=config.get('description', f"Updated from UI: {config.get('label', '')}")))
        
        # Create a comment about the logic
        logic_comment = ast.Expr(value=ast.Constant(value=f"Logic: {config.get('logic', 'Not specified')}"))
        
        # Create a placeholder for state updates
        state_updates = []
        if config.get('stateUpdates'):
            for key, value in config['stateUpdates'].items():
                # Create: state[key] = value
                assign_stmt = ast.Assign(
                    targets=[ast.Subscript(
                        value=ast.Name(id='state', ctx=ast.Load()),
                        slice=ast.Constant(value=key),
                        ctx=ast.Store()
                    )],
                    value=ast.Constant(value=str(value))
                )
                state_updates.append(assign_stmt)
        
        # Create return statement
        return_stmt = ast.Return(value=ast.Name(id='state', ctx=ast.Load()))
        
        # Combine all parts
        body = [docstring, logic_comment] + state_updates + [return_stmt]
        return body


class StateDefinitionUpdater(ast.NodeTransformer):
    """Handles updating the AgentState TypedDict based on UI configuration."""
    
    def __init__(self, state_fields: List[Dict]):
        self.state_fields = {field['name']: field for field in state_fields}
    
    def visit_ClassDef(self, node):
        """Update the AgentState class definition."""
        if node.name == "AgentState":
            # Collect existing fields to preserve them
            existing_fields = {}
            for item in node.body:
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                    existing_fields[item.target.id] = item
            
            # Add new fields from configuration
            for field_name, field_info in self.state_fields.items():
                if field_name not in existing_fields:
                    # Create new annotation assignment
                    annotation = ast.Subscript(
                        value=ast.Name(id=field_info.get('type_annotation', 'Any'), ctx=ast.Load()),
                        slice=ast.Constant(value=field_info.get('subtype', '')) if field_info.get('subtype') else None,
                        ctx=ast.Store()
                    ) if field_info.get('type_annotation') != 'Any' else ast.Name(id='Any', ctx=ast.Load())
                    
                    new_field = ast.AnnAssign(
                        target=ast.Name(id=field_name, ctx=ast.Store()),
                        annotation=annotation,
                        value=ast.Constant(value=field_info.get('default_value')),
                        simple=1
                    )
                    
                    # Add a comment/docstring for the field
                    comment = ast.Expr(value=ast.Constant(value=field_info.get('description', f"Added from UI: {field_name}")))
                    node.body.insert(0, comment)
                    node.body.append(new_field)
        
        return self.generic_visit(node)


class GraphDefinitionUpdater(ast.NodeTransformer):
    """Handles updating the graph definition in create_enhanced_agent_graph function."""
    
    def __init__(self, nodes: List[Dict], edges: List[Dict], conditional_edges: List[Dict]):
        self.nodes = {node['id']: node for node in nodes}
        self.edges = edges
        self.conditional_edges = conditional_edges
    
    def visit_FunctionDef(self, node):
        """Update the create_enhanced_agent_graph function."""
        if node.name == "create_enhanced_agent_graph":
            # Find the workflow.add_node calls and update them
            new_body = []
            i = 0
            while i < len(node.body):
                stmt = node.body[i]
                
                # If it's a workflow.add_node call, we'll replace all of them
                if (isinstance(stmt, ast.Expr) and 
                    isinstance(stmt.value, ast.Call) and 
                    isinstance(stmt.value.func, ast.Attribute) and 
                    stmt.value.func.attr == "add_node"):
                    
                    # Skip all existing add_node calls
                    while (i < len(node.body) and 
                           isinstance(node.body[i], ast.Expr) and 
                           isinstance(node.body[i].value, ast.Call) and 
                           isinstance(node.body[i].value.func, ast.Attribute) and 
                           node.body[i].value.func.attr == "add_node"):
                        i += 1
                    
                    # Add new add_node calls based on our configuration
                    for node_id, node_config in self.nodes.items():
                        add_node_call = ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='workflow', ctx=ast.Load()),
                                    attr='add_node',
                                    ctx=ast.Load()
                                ),
                                args=[
                                    ast.Constant(value=node_id),
                                    ast.Name(id=node_config.get('nodeFunction', node_id), ctx=ast.Load())
                                ],
                                keywords=[]
                            )
                        )
                        new_body.append(add_node_call)
                    
                    continue  # Don't increment i, process next statement
                
                # If it's a workflow.add_edge call, we'll replace all of them
                elif (isinstance(stmt, ast.Expr) and 
                      isinstance(stmt.value, ast.Call) and 
                      isinstance(stmt.value.func, ast.Attribute) and 
                      stmt.value.func.attr == "add_edge"):
                    
                    # Skip all existing add_edge calls
                    while (i < len(node.body) and 
                           isinstance(node.body[i], ast.Expr) and 
                           isinstance(node.body[i].value, ast.Call) and 
                           isinstance(node.body[i].value.func, ast.Attribute) and 
                           node.body[i].value.func.attr == "add_edge"):
                        i += 1
                    
                    # Add new add_edge calls based on our configuration
                    for edge in self.edges:
                        add_edge_call = ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='workflow', ctx=ast.Load()),
                                    attr='add_edge',
                                    ctx=ast.Load()
                                ),
                                args=[
                                    ast.Constant(value=edge['source']),
                                    ast.Constant(value=edge['target'])
                                ],
                                keywords=[]
                            )
                        )
                        new_body.append(add_edge_call)
                    
                    continue  # Don't increment i, process next statement
                
                # If it's a workflow.add_conditional_edges call, we'll replace all of them
                elif (isinstance(stmt, ast.Expr) and 
                      isinstance(stmt.value, ast.Call) and 
                      isinstance(stmt.value.func, ast.Attribute) and 
                      stmt.value.func.attr == "add_conditional_edges"):
                    
                    # Skip all existing add_conditional_edges calls
                    while (i < len(node.body) and 
                           isinstance(node.body[i], ast.Expr) and 
                           isinstance(node.body[i].value, ast.Call) and 
                           isinstance(node.body[i].value.func, ast.Attribute) and 
                           node.body[i].value.func.attr == "add_conditional_edges"):
                        i += 1
                    
                    # Add new add_conditional_edges calls based on our configuration
                    for cond_edge in self.conditional_edges:
                        # Create the mapping dict for conditional edges
                        mapping_dict = ast.Dict(
                            keys=[ast.Constant(value=target) for target in cond_edge['mapping'].values()],
                            values=[ast.Constant(value=target) for target in cond_edge['mapping'].values()]
                        )
                        
                        add_cond_edge_call = ast.Expr(
                            value=ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id='workflow', ctx=ast.Load()),
                                    attr='add_conditional_edges',
                                    ctx=ast.Load()
                                ),
                                args=[
                                    ast.Constant(value=cond_edge['source']),
                                    ast.Name(id=cond_edge['condition_func'], ctx=ast.Load()),
                                    mapping_dict
                                ],
                                keywords=[]
                            )
                        )
                        new_body.append(add_cond_edge_call)
                    
                    continue  # Don't increment i, process next statement
                
                new_body.append(stmt)
                i += 1
            
            node.body = new_body
        
        return self.generic_visit(node)


class CodeModifier:
    """Main class to coordinate all code modifications."""
    
    def __init__(self, target_file: str):
        self.target_file = Path(target_file)
        self.backup_manager = BackupManager()
    
    def apply_changes(self, workflow_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply changes from the UI to the target LangGraph file.
        
        Args:
            workflow_config: Dictionary containing the workflow configuration from the UI
            
        Returns:
            Dictionary with result of the operation
        """
        try:
            # Create a backup of the original file
            backup_path = self.backup_manager.create_backup(self.target_file)
            
            # Parse the original file
            with open(self.target_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code)
            
            # Extract information from the workflow config
            nodes = workflow_config.get('nodes', [])
            edges = workflow_config.get('edges', [])
            
            # Identify conditional edges from node configurations
            conditional_edges = []
            for node in nodes:
                if node.get('data', {}).get('conditionalEdges'):
                    for cond_edge in node['data']['conditionalEdges']:
                        conditional_edges.append({
                            'source': node['id'],
                            'condition_func': f"{node['data'].get('nodeFunction', node['id'])}_router",
                            'mapping': {cond_edge['condition']: cond_edge['target']}
                        })
            
            # Collect all state fields from node configurations
            state_fields = {}
            for node in nodes:
                if node.get('data', {}).get('stateUpdates'):
                    for field_name, field_value in node['data']['stateUpdates'].items():
                        state_fields[field_name] = {
                            'name': field_name,
                            'type_annotation': 'Any',
                            'default_value': field_value,
                            'description': f"Field added from UI configuration for {node['id']}"
                        }
            
            # Apply transformations
            # 1. Update node functions
            node_updater = NodeFunctionUpdater(nodes)
            tree = node_updater.visit(tree)
            
            # 2. Update state definition
            state_updater = StateDefinitionUpdater(list(state_fields.values()))
            tree = state_updater.visit(tree)
            
            # 3. Update graph definition
            graph_updater = GraphDefinitionUpdater(nodes, edges, conditional_edges)
            tree = graph_updater.visit(tree)
            
            # Write the modified code back to the file
            try:
                modified_code = astor.to_source(tree)
            except Exception as e:
                # If astor fails, try using ast.unparse (available in Python 3.9+)
                try:
                    import sys
                    if sys.version_info >= (3, 9):
                        modified_code = ast.unparse(tree)
                    else:
                        # If neither works, preserve original
                        raise e
                except Exception:
                    raise e

            with open(self.target_file, 'w', encoding='utf-8') as f:
                f.write(modified_code)
            
            return {
                'status': 'success',
                'message': f'Changes successfully applied to {self.target_file}',
                'backup_path': backup_path
            }
            
        except Exception as e:
            # If there's an error, restore from backup
            try:
                if 'backup_path' in locals():
                    self.backup_manager.restore_from_backup(self.target_file, backup_path)
            except:
                pass  # If restoration fails, at least preserve the original error
            
            return {
                'status': 'error',
                'message': f'Error applying changes: {str(e)}',
                'backup_path': backup_path if 'backup_path' in locals() else None
            }


# Example usage
if __name__ == "__main__":
    # Example workflow configuration from the UI
    example_workflow = {
        "name": "ExampleWorkflow",
        "nodes": [
            {
                "id": "start_node",
                "data": {
                    "label": "Start Node",
                    "description": "Starting point of the workflow",
                    "nodeFunction": "start_node",
                    "logic": "Initialize workflow state",
                    "stateUpdates": {
                        "user_request": "state['user_request']",
                        "step_count": 0
                    }
                }
            },
            {
                "id": "process_node",
                "data": {
                    "label": "Process Node",
                    "description": "Processes the input",
                    "nodeFunction": "process_node",
                    "logic": "Process the input data",
                    "stateUpdates": {
                        "processed_data": "process(input_data)",
                        "status": "completed"
                    },
                    "conditionalEdges": [
                        {
                            "condition": "data_valid",
                            "target": "output_node"
                        },
                        {
                            "condition": "not data_valid", 
                            "target": "error_node"
                        }
                    ]
                }
            }
        ],
        "edges": [
            {
                "source": "start_node",
                "target": "process_node"
            }
        ]
    }
    
    # Apply changes to the target file
    modifier = CodeModifier("../../langgraph_agent/langgraph_agent.py")
    result = modifier.apply_changes(example_workflow)
    print(json.dumps(result, indent=2))