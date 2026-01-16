#!/usr/bin/env python3
"""
Demo script showcasing the new Security LLM prompt functionality
"""

from models.security_sql_detector import SecuritySQLDetector
from utils.prompt_manager import PromptManager


def demo_security_prompt_loading():
    """Demonstrate that the security prompt is properly loaded from external file"""
    print("=== Demo: Security Prompt Loading ===")
    
    # Show available prompts
    pm = PromptManager()
    prompts = pm.list_prompts()
    print(f"Available prompts: {prompts}")
    
    # Get the security prompt
    security_prompt = pm.get_prompt('security_sql_analysis')
    if security_prompt:
        print(f"✓ Security prompt loaded successfully")
        print(f"  Length: {len(security_prompt)} characters")
        print(f"  Preview: {security_prompt[:100]}...")
    else:
        print("✗ Failed to load security prompt")
    
    print()


def demo_security_detector_with_prompt():
    """Demonstrate the security detector using the external prompt"""
    print("=== Demo: Security Detector with External Prompt ===")
    
    # Create detector instance
    detector = SecuritySQLDetector()
    print("✓ Security detector initialized with external prompt")
    
    # Test with a safe query
    safe_query = "SELECT * FROM users WHERE created_at > '2023-01-01';"
    print(f"Testing safe query: {safe_query[:50]}...")
    
    result = detector.analyze_query(safe_query)
    print(f"Analysis result: {result}")
    
    # Test with a potentially harmful query
    harmful_query = "SELECT * FROM users; DROP TABLE users;"
    print(f"Testing potentially harmful query: {harmful_query[:50]}...")
    
    result = detector.analyze_query(harmful_query)
    print(f"Analysis result: {result}")
    
    print()


def demo_prompt_editing_capability():
    """Demonstrate that the prompt can be edited via the prompt editor"""
    print("=== Demo: Prompt Editing Capability ===")
    
    pm = PromptManager()
    
    # Show how to update the prompt
    print("The security prompt can be edited using the prompt editor:")
    print("  python prompt_editor.py")
    print("  Select option 3 (Edit an existing prompt)")
    print("  Enter 'security_sql_analysis' as the prompt name")
    print()
    
    # Show current prompt content
    current_prompt = pm.get_prompt('security_sql_analysis')
    print(f"Current prompt length: {len(current_prompt)} characters")
    
    # Check if it contains key elements
    has_security_expert = "security expert" in current_prompt.lower()
    has_vulnerability_assessment = "vulnerability assessment" in current_prompt.lower()
    has_json_instruction = "json" in current_prompt.lower()
    
    print(f"✓ Contains 'security expert': {has_security_expert}")
    print(f"✓ Contains 'vulnerability assessment': {has_vulnerability_assessment}")
    print(f"✓ Contains 'JSON' instructions: {has_json_instruction}")
    
    print()


if __name__ == "__main__":
    print("Security LLM Prompt Demo\n")
    
    demo_security_prompt_loading()
    demo_security_detector_with_prompt()
    demo_prompt_editing_capability()
    
    print("Summary:")
    print("- Security prompt is loaded from external file (prompts/security_sql_analysis.txt)")
    print("- The prompt can be modified without changing code")
    print("- The prompt editor utility supports editing the security prompt")
    print("- Security detector uses the external prompt for analysis")
    print("- Fallback mechanism ensures security even if LLM fails")