#!/usr/bin/env python3
"""
Test script to verify the updated retry logic for SQL generation with wider search.
This script tests the new requirements:
1. If generated SQL execution followed by errors - we need to call wider search analysis until no errors found in generated sql.
2. If no results returned, we need to do 10 attempts to use wider search analysis.
"""

import sys
import os

# Add the project root to the path so we can import modules
sys.path.insert(0, '/root/qwen_test/ai_agent')

from langgraph_agent.langgraph_agent import AgentState, should_execute_wider_search, should_refine_or_respond, should_retry, should_validate_after_security_check

def test_should_execute_wider_search():
    """Test the should_execute_wider_search function with execution errors"""
    print("Testing should_execute_wider_search with execution errors...")

    # Test case 1: Execution error present, should go to wider search
    state_with_error = {
        "db_results": [{"id": 1, "name": "test"}],  # Has results
        "execution_error": "Some execution error occurred",
        "query_type": "initial",
        "retry_count": 0
    }

    result = should_execute_wider_search(state_with_error)
    assert result == "wider_search", f"Expected 'wider_search', got '{result}'"
    print("✓ Execution error triggers wider search even when results exist")

    # Test case 2: No execution error, no results, should go to wider search
    state_no_results = {
        "db_results": [],  # No results
        "execution_error": None,
        "query_type": "initial",
        "retry_count": 0
    }

    result = should_execute_wider_search(state_no_results)
    assert result == "wider_search", f"Expected 'wider_search', got '{result}'"
    print("✓ No results triggers wider search")

    # Test case 3: No execution error, has results, should respond
    state_has_results = {
        "db_results": [{"id": 1, "name": "test"}],  # Has results
        "execution_error": None,
        "query_type": "initial",
        "retry_count": 0
    }

    result = should_execute_wider_search(state_has_results)
    assert result == "respond", f"Expected 'respond', got '{result}'"
    print("✓ Has results triggers response generation")


def test_should_refine_or_respond():
    """Test the should_refine_or_respond function"""
    print("\nTesting should_refine_or_respond...")

    # Test case 1: Validation error present, should refine
    state_with_validation_error = {
        "validation_error": "Some validation error",
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_refine_or_respond(state_with_validation_error)
    assert result == "refine", f"Expected 'refine', got '{result}'"
    print("✓ Validation error triggers refinement")

    # Test case 2: Execution error present, should refine
    state_with_execution_error = {
        "validation_error": None,
        "execution_error": "Some execution error",
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_refine_or_respond(state_with_execution_error)
    assert result == "refine", f"Expected 'refine', got '{result}'"
    print("✓ Execution error triggers refinement")

    # Test case 3: SQL generation error present, should refine
    state_with_generation_error = {
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": "Some generation error",
        "retry_count": 5
    }

    result = should_refine_or_respond(state_with_generation_error)
    assert result == "refine", f"Expected 'refine', got '{result}'"
    print("✓ SQL generation error triggers refinement")

    # Test case 4: No errors, should respond
    state_no_errors = {
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_refine_or_respond(state_no_errors)
    assert result == "respond", f"Expected 'respond', got '{result}'"
    print("✓ No errors triggers response generation")

    # Test case 5: Max attempts reached, should respond regardless of errors
    state_max_attempts = {
        "validation_error": "Some validation error",
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 10  # At max attempts
    }

    result = should_refine_or_respond(state_max_attempts)
    assert result == "respond", f"Expected 'respond', got '{result}'"
    print("✓ Max attempts reached triggers response generation")


def test_should_retry():
    """Test the should_retry function"""
    print("\nTesting should_retry...")

    # Test case 1: Validation error present, should retry
    state_with_validation_error = {
        "validation_error": "Some validation error",
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_retry(state_with_validation_error)
    assert result == "yes", f"Expected 'yes', got '{result}'"
    print("✓ Validation error triggers retry")

    # Test case 2: Execution error present, should retry
    state_with_execution_error = {
        "validation_error": None,
        "execution_error": "Some execution error",
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_retry(state_with_execution_error)
    assert result == "yes", f"Expected 'yes', got '{result}'"
    print("✓ Execution error triggers retry")

    # Test case 3: SQL generation error present, should retry
    state_with_generation_error = {
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": "Some generation error",
        "retry_count": 5
    }

    result = should_retry(state_with_generation_error)
    assert result == "yes", f"Expected 'yes', got '{result}'"
    print("✓ SQL generation error triggers retry")

    # Test case 4: No errors, should not retry
    state_no_errors = {
        "validation_error": None,
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 5
    }

    result = should_retry(state_no_errors)
    assert result == "no", f"Expected 'no', got '{result}'"
    print("✓ No errors does not trigger retry")

    # Test case 5: Max attempts reached, should not retry regardless of errors
    state_max_attempts = {
        "validation_error": "Some validation error",
        "execution_error": None,
        "sql_generation_error": None,
        "retry_count": 10  # At max attempts
    }

    result = should_retry(state_max_attempts)
    assert result == "no", f"Expected 'no', got '{result}'"
    print("✓ Max attempts reached does not trigger retry")


def test_should_validate_after_security_check():
    """Test the should_validate_after_security_check function"""
    print("\nTesting should_validate_after_security_check...")

    # Test case 1: Validation error present, should refine
    state_with_error = {
        "validation_error": "Some validation error after security check",
        "retry_count": 5
    }

    result = should_validate_after_security_check(state_with_error)
    assert result == "refine", f"Expected 'refine', got '{result}'"
    print("✓ Validation error after security check triggers refinement")

    # Test case 2: No validation error, should respond
    state_no_error = {
        "validation_error": None,
        "retry_count": 5
    }

    result = should_validate_after_security_check(state_no_error)
    assert result == "respond", f"Expected 'respond', got '{result}'"
    print("✓ No validation error after security check triggers response")

    # Test case 3: Max attempts reached, should respond regardless of errors
    state_max_attempts = {
        "validation_error": "Some validation error after security check",
        "retry_count": 10  # At max attempts
    }

    result = should_validate_after_security_check(state_max_attempts)
    assert result == "respond", f"Expected 'respond', got '{result}'"
    print("✓ Max attempts reached triggers response generation")


def main():
    """Run all tests"""
    print("Running tests for updated retry logic...\n")

    test_should_execute_wider_search()
    test_should_refine_or_respond()
    test_should_retry()
    test_should_validate_after_security_check()

    print("\n✅ All tests passed! The updated retry logic is working correctly.")


if __name__ == "__main__":
    main()