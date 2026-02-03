#!/usr/bin/env python3
"""
Analyze and visualize the langgraph workflow logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def analyze_langgraph_workflow():
    """
    Analyze the langgraph workflow based on the code structure
    """
    print("LANGGRAPH AGENT WORKFLOW ANALYSIS")
    print("="*60)
    
    print("\nNODES IN THE WORKFLOW:")
    print("-" * 30)
    nodes = [
        "initialize_agent_state",
        "discover_services", 
        "analyze_request",
        "check_mcp_applicability",
        "retrieve_documents",
        "process_search_results_with_download",
        "rerank_documents",
        "augment_context",
        "generate_rag_response",
        "plan_mcp_queries",
        "execute_mcp_queries",
        "synthesize_results",
        "can_answer",
        "generate_final_answer",
        "plan_refined_queries",
        "generate_failure_response",
        "generate_final_answer_from_analysis",
        "generate_failure_response_from_analysis"
    ]
    
    for i, node in enumerate(nodes, 1):
        print(f"{i:2d}. {node}")
    
    print("\nWORKFLOW LOGICAL FLOW:")
    print("-" * 30)
    print("""
INITIAL PHASE:
┌─────────────────────────┐
│ initialize_agent_state  │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│   discover_services     │
└─────────────────────────┘
           │
           ▼
┌─────────────────────────┐
│    analyze_request      │
└─────────────────────────┘
           │
           ▼
    ┌─────────────┐ is_final_answer?
    │             ├─────────────────────────────────┐
    └─────────────┘                                 │
         │ Yes                                      │
         ▼                                         │
┌─────────────────────────┐                        │
│generate_final_answer    │                        │
│   _from_analysis        │                        │
└─────────────────────────┘                        │
         │                                         │
         ▼                                         │
        END ←──────────────────────────────────────┘
         ↑
         │
┌─────────────────────────┐
│generate_failure_response│
│   _from_analysis        │
└─────────────────────────┘
         ▲
         │
         │ No MCP tool calls & not final answer
    ┌─────────────┐ has_mcp_tool_calls?
    │             ├─────────────────────────┐
    └─────────────┘                         │
         │                                  │
         ▼                                  │
┌─────────────────────────┐                 │
│ check_mcp_applicability │                 │
└─────────────────────────┘                 │
           │                                 │
           ▼                                 │
    ┌─────────────┐ use_rag?                │
    │             ├─────────────┬───────────┘
    └─────────────┘             │ Yes
         │ No                   │
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ plan_mcp_queries│    │retrieve_documen-│
└─────────────────┘    │     ts        │
         │              └─────────────────┘
         ▼                       │
┌─────────────────┐              ▼
│execute_mcp_quer-│    ┌─────────────────┐
│     ies         │    │ rerank_documen- │
└─────────────────┘    │     ts        │
         │              └─────────────────┘
         ▼                       │
┌─────────────────┐              ▼
│synthesize_resul-│    ┌─────────────────┐
│     ts          │    │augment_context  │
└─────────────────┘    └─────────────────┘
         │                       │
         ▼                       ▼
    ┌─────────────┐    ┌─────────────────┐
    │             │    │generate_rag_res-│
    │ can_answer? │    │     ponse       │
    │             │    └─────────────────┘
    └─────────────┘             │
         │ │ │                  ▼
         │ │ └──────────► can_answer? ──┐
         │ │                      │     │
         │ │                      ▼     │
         │ │            ┌─────────────────┐ │
         │ │            │generate_final_  │ │
         │ │            │     answer      │ │
         │ │            └─────────────────┘ │
         │ │                      │         │
         │ │                      ▼         │
         │ │                     END ◄──────┘
         │ │
         │ └─► plan_refined_queries ──► execute_mcp_queries ──► ...
         │
         └─► generate_failure_response ──► END

""")
    
    print("\nCONDITIONAL BRANCHES AND DECISION POINTS:")
    print("-" * 40)
    
    print("\n1. check_is_final_answer (after analyze_request):")
    print("   - If is_final_answer=True and no MCP tool calls → generate_final_answer_from_analysis")
    print("   - If is_final_answer=False and no MCP tool calls → generate_failure_response_from_analysis")
    print("   - If has MCP tool calls → check_mcp_applicability")
    
    print("\n2. should_use_rag (after check_mcp_applicability):")
    print("   - If non-RAG calls exist → use_mcp (plan_mcp_queries)")
    print("   - If only RAG calls exist → use_rag (retrieve_documents)")
    print("   - If no MCP services identified → use_rag (fallback)")
    
    print("\n3. should_process_search_results (after synthesize_results):")
    print("   - If search results found in raw data → process_with_download")
    print("   - If no search results → skip_processing (go to can_answer)")
    
    print("\n4. should_iterate_or_use_rag (after can_answer):")
    print("   - If RAG was originally requested and can't answer → use_rag")
    print("   - If can_answer=True → generate_final_answer")
    print("   - If iteration_count < max_iterations → plan_refined_queries")
    print("   - Otherwise → generate_failure_response")
    
    print("\nKEY STATE FIELDS:")
    print("-" * 20)
    state_fields = {
        "user_request": "Original user request",
        "mcp_queries": "Planned MCP queries to execute",
        "mcp_results": "Results from executed MCP queries",
        "mcp_tool_calls": "Tool calls from LLM analysis",
        "synthesized_result": "Synthesized result from multiple queries",
        "can_answer": "Flag indicating if we can answer",
        "iteration_count": "Number of iterations performed",
        "max_iterations": "Maximum allowed iterations",
        "final_answer": "Final answer to return",
        "is_final_answer": "Flag from LLM if this is a final answer",
        "rag_documents": "Documents retrieved from RAG",
        "rag_context": "Augmented context with RAG documents",
        "raw_mcp_results": "Raw results before normalization"
    }
    
    for field, desc in state_fields.items():
        print(f"- {field:<20}: {desc}")
    
    print("\nPOTENTIAL ISSUES IDENTIFIED:")
    print("-" * 30)
    issues = [
        "1. State field reducers: Previously using operator.add for fields that should be replaced",
        "2. Iteration logic: Complex branching that could lead to infinite loops",
        "3. RAG vs MCP decision: Multiple pathways that might not be clearly separated",
        "4. Error handling: Several nodes could fail and affect downstream processing"
    ]
    
    for issue in issues:
        print(issue)
    
    print("\nFIX APPLIED:")
    print("-" * 15)
    print("Fixed state field reducers for mcp_queries, mcp_tool_calls, raw_mcp_results,")
    print("and refined_queries to use replacement (lambda x, y: y) instead of appending")
    print("(operator.add) to prevent multiplication of tool calls.")


def simulate_workflow_scenario():
    """
    Simulate a typical workflow scenario based on the log provided
    """
    print("\nTYPICAL WORKFLOW SCENARIO SIMULATION:")
    print("-" * 40)
    print("Input: 'найди в RAG и интернете требования к малым базам биометрических образов Чужой'")
    
    scenario_steps = [
        ("1. initialize_agent_state", "Initialize state with user request"),
        ("2. discover_services", "Discover available MCP services"),
        ("3. analyze_request", "LLM analyzes request and returns 3 tool calls:"),
        ("   ", "   - rag-server query_documents"),
        ("   ", "   - search-server web_search"), 
        ("   ", "   - sql-server get_schema"),
        ("4. check_mcp_applicability", "Check if MCP services are applicable"),
        ("5. plan_mcp_queries", "Plan the 3 queries (should remain 3, not multiply)"),
        ("6. execute_mcp_queries", "Execute the 3 queries (should remain 3, not multiply)"),
        ("7. synthesize_results", "Combine results from all queries"),
        ("8. can_answer", "Evaluate if results adequately answer the request"),
        ("9. generate_final_answer", "Generate final response based on results")
    ]
    
    for step, desc in scenario_steps:
        print(f"{step:<30} {desc}")
        
    print("\nEXPECTED BEHAVIOR AFTER FIX:")
    print("-" * 35)
    print("• Original 3 tool calls remain as 3 throughout the process")
    print("• No multiplication to 6 during planning phase")
    print("• No multiplication to 12 during execution phase")
    print("• Proper state management with replacement instead of accumulation")


if __name__ == "__main__":
    analyze_langgraph_workflow()
    simulate_workflow_scenario()