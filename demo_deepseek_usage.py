"""
Demo script showing how to use DeepSeek models with the AI Agent.

To use DeepSeek models, you need to:
1. Get a DeepSeek API key from https://www.deepseek.com/
2. Set the DEEPSEEK_API_KEY environment variable
3. Configure your LLM providers to use 'DeepSeek'

Example usage:
export DEEPSEEK_API_KEY=your_deepseek_api_key_here
export SQL_LLM_PROVIDER=DeepSeek
export RESPONSE_LLM_PROVIDER=DeepSeek
export PROMPT_LLM_PROVIDER=DeepSeek
export SECURITY_LLM_PROVIDER=DeepSeek
python ai_agent.py
"""

import os
from ai_agent import AIAgent

def demo_deepseek_usage():
    print("DeepSeek AI Agent Demo")
    print("=" * 40)
    
    # Show current configuration
    print(f"Current SQL LLM Provider: {os.getenv('SQL_LLM_PROVIDER', 'Not Set')}")
    print(f"Current Response LLM Provider: {os.getenv('RESPONSE_LLM_PROVIDER', 'Not Set')}")
    print(f"Current Prompt LLM Provider: {os.getenv('PROMPT_LLM_PROVIDER', 'Not Set')}")
    print(f"Current Security LLM Provider: {os.getenv('SECURITY_LLM_PROVIDER', 'Not Set')}")
    print(f"DeepSeek API Key configured: {'Yes' if os.getenv('DEEPSEEK_API_KEY') else 'No'}")
    print()
    
    # Example of how to configure for DeepSeek programmatically
    print("Configuring for DeepSeek...")
    os.environ['SQL_LLM_PROVIDER'] = 'DeepSeek'
    os.environ['RESPONSE_LLM_PROVIDER'] = 'DeepSeek'
    os.environ['PROMPT_LLM_PROVIDER'] = 'DeepSeek'
    os.environ['SECURITY_LLM_PROVIDER'] = 'DeepSeek'
    
    # Note: In practice, you would set DEEPSEEK_API_KEY to your actual API key
    # os.environ['DEEPSEEK_API_KEY'] = 'your-actual-api-key-here'
    
    print("Providers set to DeepSeek")
    print(f"SQL LLM Provider: {os.getenv('SQL_LLM_PROVIDER')}")
    print(f"Response LLM Provider: {os.getenv('RESPONSE_LLM_PROVIDER')}")
    print()
    
    print("Initializing AI Agent with DeepSeek configuration...")
    try:
        # Initialize the agent (this will use the environment variables we just set)
        agent = AIAgent()
        
        print("✓ AI Agent initialized successfully with DeepSeek configuration!")
        print()
        
        print("Example usage:")
        print("agent.process_request('Show me all users')")
        print()
        
        print("Note: To actually use DeepSeek, you need to:")
        print("1. Sign up at https://www.deepseek.com/ to get an API key")
        print("2. Set the DEEPSEEK_API_KEY environment variable")
        print("3. Optionally, update your .env file with the configuration")
        print()
        
        print("Example .env configuration for DeepSeek:")
        print("# DeepSeek Configuration")
        print("DEEPSEEK_API_KEY=your-api-key-here")
        print("SQL_LLM_PROVIDER=DeepSeek")
        print("SQL_LLM_MODEL=deepseek-chat")  # or deepseek-coder for coding tasks
        print("SQL_LLM_HOSTNAME=api.deepseek.com")
        print("SQL_LLM_PORT=443")
        print("SQL_LLM_API_PATH=/v1")
        print()
        print("RESPONSE_LLM_PROVIDER=DeepSeek")
        print("RESPONSE_LLM_MODEL=deepseek-chat")
        print("RESPONSE_LLM_HOSTNAME=api.deepseek.com")
        print("RESPONSE_LLM_PORT=443")
        print("RESPONSE_LLM_API_PATH=/v1")
        print()
        print("PROMPT_LLM_PROVIDER=DeepSeek")
        print("PROMPT_LLM_MODEL=deepseek-chat")
        print("PROMPT_LLM_HOSTNAME=api.deepseek.com")
        print("PROMPT_LLM_PORT=443")
        print("PROMPT_LLM_API_PATH=/v1")
        print()
        print("SECURITY_LLM_PROVIDER=DeepSeek")
        print("SECURITY_LLM_MODEL=deepseek-chat")
        print("SECURITY_LLM_HOSTNAME=api.deepseek.com")
        print("SECURITY_LLM_PORT=443")
        print("SECURITY_LLM_API_PATH=/v1")
        
    except Exception as e:
        print(f"✗ Error initializing AI Agent: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demo_deepseek_usage()