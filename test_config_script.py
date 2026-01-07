#!/usr/bin/env python3
"""
Test script to verify the configuration script works correctly.
"""

import os
import sys
from pathlib import Path
import tempfile
import subprocess


def test_config_script():
    """Test the configuration script by simulating user inputs."""
    project_root = Path(__file__).parent
    setup_script = project_root / "setup_config.py"
    test_env_file = project_root / ".env.test"
    
    # Create a temporary .env file with test values
    test_input = """postgresql://testuser:testpass@localhost:5432/testdb
sk-testapikey12345
gpt-4-test
gpt-3.5-turbo-test
gpt-4-test
"""
    
    # Save the original .env if it exists
    original_env = project_root / ".env"
    backup_env = project_root / ".env.backup"
    if original_env.exists():
        original_env.rename(backup_env)
    
    try:
        # Run the setup script with test inputs
        with open(setup_script, 'r') as f:
            script_content = f.read()
        
        # Create a test environment
        env_file_path = project_root / ".env"
        
        # Write test inputs to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_input:
            temp_input.write(test_input)
            temp_input_path = temp_input.name
        
        # Run the setup script with the test inputs
        with open(temp_input_path, 'r') as input_file:
            result = subprocess.run(
                [sys.executable, str(setup_script)],
                stdin=input_file,
                capture_output=True,
                text=True,
                cwd=project_root
            )
        
        # Clean up the temporary input file
        os.unlink(temp_input_path)
        
        print("Setup script output:")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)
        print("Return code:", result.returncode)
        
        # Check if .env file was created
        if env_file_path.exists():
            print("\n✓ .env file was created successfully")
            
            # Read and display the contents of the created .env file
            with open(env_file_path, 'r') as env_file:
                env_content = env_file.read()
                print("\nContents of .env file:")
                print(env_content)
                
            # Verify expected values are in the file
            expected_values = [
                "DATABASE_URL=postgresql://testuser:testpass@localhost:5432/testdb",
                "OPENAI_API_KEY=sk-testapikey12345",
                "SQL_LLM_MODEL=gpt-4-test",
                "RESPONSE_LLM_MODEL=gpt-3.5-turbo-test",
                "PROMPT_LLM_MODEL=gpt-4-test"
            ]
            
            all_found = True
            for value in expected_values:
                if value not in env_content:
                    print(f"✗ Expected value not found in .env: {value}")
                    all_found = False
                else:
                    print(f"✓ Found expected value: {value}")
            
            if all_found:
                print("\n✓ All expected values found in .env file")
            else:
                print("\n✗ Some expected values are missing from .env file")
        else:
            print("\n✗ .env file was not created")
            
    finally:
        # Restore the original .env if it existed
        if backup_env.exists():
            backup_env.rename(original_env)
        elif original_env.exists():
            # If we created a new .env file during testing, remove it
            original_env.unlink()
    

if __name__ == "__main__":
    test_config_script()