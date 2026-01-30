#!/usr/bin/env python3
"""
Corrected version of the synthesize_results_node that properly handles MCP service responses
"""
def corrected_synthesize_results_node(state):
    """
    Corrected node to synthesize results from multiple MCP queries
    """
    import time
    import logging
    from models.response_generator import ResponseGenerator
    
    start_time = time.time()
    logger = logging.getLogger(__name__)
    logger.info(f"Synthesizing {len(state['mcp_results'])} results")

    try:
        # Import required components
        response_generator = ResponseGenerator()

        # If we have no results, return an empty synthesis
        if not state["mcp_results"]:
            logger.info("No results to synthesize")

            elapsed_time = time.time() - start_time
            logger.info(f"Synthesized results in {elapsed_time:.2f}s")

            return {
                **state,
                "synthesized_result": "No results were obtained from the MCP services."
            }

        # Prepare the results for synthesis
        formatted_results = []
        for idx, result in enumerate(state["mcp_results"]):
            formatted_result = f"Result {idx + 1}: "
            if result.get("status") == "success":
                # Handle different response formats
                result_data = result.get('result')  # This is where MCP service responses store data
                
                if result_data and isinstance(result_data, dict):
                    # Check if this is a search service response
                    if 'results' in result_data:
                        # This is likely a search service response with actual search results
                        search_results = result_data['results']
                        formatted_result += f"Success - Found {len(search_results)} search results:\n"
                        for i, search_result in enumerate(search_results[:5]):  # Limit to first 5 results
                            title = search_result.get('title', 'No Title')
                            snippet = search_result.get('description', search_result.get('content', ''))[:200] + "..." if len(search_result.get('description', search_result.get('content', ''))) > 200 else search_result.get('description', search_result.get('content', ''))
                            formatted_result += f"  {i+1}. {title}\n     {snippet}\n"
                    elif 'success' in result_data and 'query' in result_data:
                        # This is a search service response format
                        search_results = result_data.get('results', [])
                        formatted_result += f"Success - Search for '{result_data.get('query', 'unknown query')}' returned {len(search_results)} results:\n"
                        for i, search_result in enumerate(search_results[:5]):  # Limit to first 5 results
                            title = search_result.get('title', 'No Title')
                            snippet = search_result.get('description', search_result.get('content', ''))[:200] + "..." if len(search_result.get('description', search_result.get('content', ''))) > 200 else search_result.get('description', search_result.get('content', ''))
                            formatted_result += f"  {i+1}. {title}\n     {snippet}\n"
                    else:
                        # Generic handling for other types of service responses
                        formatted_result += f"Success - {str(result_data)}"
                else:
                    # Fallback to original behavior if result is not a dict or is None
                    formatted_result += f"Success - {result.get('data', str(result))}"
            else:
                formatted_result += f"Error - {result.get('error', str(result))}"
            formatted_results.append(formatted_result)

        # Combine all results into a single string
        combined_results = "\n".join(formatted_results)

        # Create a synthesis prompt that includes the user request and all results
        synthesis_prompt = f"""
        Original request: {state["user_request"]}

        Results from MCP services:
        {combined_results}

        Please synthesize these results into a coherent response that addresses the original request.
        If the results are conflicting, please note the discrepancies.
        If the results are incomplete, please note what information is missing.
        """

        # Use the response generator to synthesize the results
        synthesized_result = response_generator.generate_natural_language_response(
            synthesis_prompt
        )

        elapsed_time = time.time() - start_time
        logger.info(f"Synthesized results into response")

        return {
            **state,
            "synthesized_result": synthesized_result
        }
    except Exception as e:
        elapsed_time = time.time() - start_time
        error_msg = f"Error synthesizing results: {str(e)}"
        logger.error(f"Error synthesizing results after {elapsed_time:.2f}s: {str(e)}")

        return {
            **state,
            "synthesized_result": "",
            "error_message": error_msg
        }

# Test the corrected function with sample data
sample_result = {
    "service_id": "search-server-127-0-0-1-8090",
    "status": "success",
    "result": {
        "success": True,
        "query": "что мы знаем про правила малых баз?",
        "results": [
            {
                "title": "Теория - Базирование - правило 6 точек",
                "url": "https://base-techmash.narod.ru/Base.htm",
                "description": "Явная база - база в виде реальной поверхности, разметочной риски или точки пересечения рисок...",
                "date": "",
                "language": "ru",
                "thumbnail": ""
            }
        ],
        "error": None
    }
}

sample_state = {
    "user_request": "что мы знаем про правила малых баз?",
    "mcp_results": [sample_result]
}

corrected_result = corrected_synthesize_results_node(sample_state)
print("Corrected synthesis result:")
print(corrected_result["synthesized_result"])