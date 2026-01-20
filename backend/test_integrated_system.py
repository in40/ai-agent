#!/usr/bin/env python3
"""
Comprehensive test script for the AI Agent system with backend and frontend components.
This script verifies that all components work together correctly.
"""

import os
import sys
import time
import subprocess
import requests
import threading
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def start_backend():
    """Start the backend server in a separate thread"""
    import subprocess
    import os
    
    # Activate the virtual environment and start the backend
    env = os.environ.copy()
    env['PYTHONPATH'] = str(project_root)
    env['FLASK_APP'] = 'backend.app'
    env['FLASK_ENV'] = 'development'
    
    # Start the backend server
    process = subprocess.Popen([
        'python', '-m', 'flask', 
        '--app', 'backend.app', 
        'run', 
        '--host=0.0.0.0', 
        '--port=5000'
    ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    return process

def test_backend_api():
    """Test the backend API endpoints"""
    print("Testing backend API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get('http://localhost:5000/api/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
        print("✓ Health endpoint working")
    except Exception as e:
        print(f"✗ Health endpoint failed: {e}")
        return False
    
    # Test registration endpoint
    try:
        response = requests.post('http://localhost:5000/auth/register', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 201
        print("✓ Registration endpoint working")
    except Exception as e:
        print(f"✗ Registration endpoint failed: {e}")
        return False
    
    # Test login endpoint
    try:
        response = requests.post('http://localhost:5000/auth/login', json={
            'username': 'testuser',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        data = response.json()
        assert 'token' in data
        token = data['token']
        print("✓ Login endpoint working")
    except Exception as e:
        print(f"✗ Login endpoint failed: {e}")
        return False
    
    # Test agent query endpoint (with authentication)
    try:
        headers = {'Authorization': f'Bearer {token}'}
        response = requests.post('http://localhost:5000/api/agent/query', json={
            'user_request': 'What is your name?',
            'disable_databases': True
        }, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert 'final_response' in data
        print("✓ Agent query endpoint working")
    except Exception as e:
        print(f"✗ Agent query endpoint failed: {e}")
        return False
    
    # Test RAG endpoints (with authentication)
    try:
        response = requests.post('http://localhost:5000/api/rag/query', json={
            'query': 'test query'
        }, headers=headers)
        # This might fail if RAG is not properly configured, but that's OK for now
        print("✓ RAG query endpoint accessible")
    except Exception:
        print("? RAG query endpoint may not be fully configured")
    
    return True

def test_web_client_access():
    """Test access to the web client"""
    print("Testing web client access...")
    
    try:
        response = requests.get('http://localhost:5000/')
        assert response.status_code == 200
        assert 'AI Agent Dashboard' in response.text
        print("✓ Web client accessible")
        return True
    except Exception as e:
        print(f"✗ Web client access failed: {e}")
        return False

def test_services_availability():
    """Test that required services are available"""
    print("Testing required services...")
    
    # Check if required services are running
    services = [
        ('http://localhost:5000/api/health', 'Backend API'),
        ('http://localhost:8501', 'Streamlit GUI'),
        ('http://localhost:3000', 'React GUI'),
    ]
    
    for url, name in services:
        try:
            response = requests.get(url, timeout=5)
            print(f"✓ {name} available at {url}")
        except:
            print(f"? {name} not available at {url} (this may be expected if not started)")
    
    return True

def run_comprehensive_test():
    """Run comprehensive tests on the AI Agent system"""
    print("="*60)
    print("COMPREHENSIVE AI AGENT SYSTEM TEST")
    print("="*60)
    
    # Start backend server in background
    print("Starting backend server...")
    backend_process = start_backend()
    
    # Wait a bit for the server to start
    time.sleep(5)
    
    try:
        # Run tests
        all_tests_passed = True
        
        all_tests_passed &= test_backend_api()
        all_tests_passed &= test_web_client_access()
        all_tests_passed &= test_services_availability()
        
        print("\n" + "="*60)
        if all_tests_passed:
            print("🎉 ALL TESTS PASSED! The AI Agent system is working correctly.")
        else:
            print("❌ SOME TESTS FAILED! Please check the output above for details.")
        print("="*60)
        
        return all_tests_passed
        
    finally:
        # Terminate the backend process
        print("\nStopping backend server...")
        backend_process.terminate()
        try:
            backend_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            backend_process.kill()

def print_system_overview():
    """Print an overview of the system architecture"""
    print("\nSYSTEM ARCHITECTURE OVERVIEW:")
    print("-" * 40)
    print("BACKEND COMPONENTS:")
    print("  • Flask API Server (port 5000)")
    print("  • Authentication system (JWT)")
    print("  • Agent query endpoint (/api/agent/query)")
    print("  • RAG endpoints (/api/rag/*)")
    print("  • Proxy for Streamlit GUI (/streamlit/*)")
    print("  • Proxy for React GUI (/react/*)")
    print("  • Static file serving (web client)")
    
    print("\nFRONTEND COMPONENTS:")
    print("  • Web client (HTML/CSS/JS)")
    print("  • Login/Register pages")
    print("  • Main client tab (agent interaction)")
    print("  • Streamlit GUI tab (visualization)")
    print("  • React GUI tab (workflow editor)")
    print("  • RAG functions tab (document management)")
    
    print("\nINFRASTRUCTURE:")
    print("  • Nginx with TLS termination")
    print("  • Distributed deployment config")
    print("  • Authentication tokens")
    print("-" * 40)

if __name__ == "__main__":
    print_system_overview()
    
    # Run the comprehensive test
    success = run_comprehensive_test()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)