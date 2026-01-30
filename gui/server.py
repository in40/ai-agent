"""
Simple server to serve the LangGraph Visual Editor interfaces
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys
import threading
import webbrowser
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class LangGraphEditorServer(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.dirname(os.path.abspath(__file__)), **kwargs)

    def do_GET(self):
        if self.path == '/':
            self.path = '/index.html'
        elif self.path == '/streamlit':
            # Redirect to the Streamlit app
            self.send_response(302)
            self.send_header('Location', 'http://localhost:8501')
            self.end_headers()
            return
        elif self.path == '/react-editor':
            # Serve a page that explains how to run the React app
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            react_info = '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>React Editor Setup</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .instructions { background-color: #f0f8ff; padding: 20px; border-radius: 5px; }
                </style>
            </head>
            <body>
                <h1>React LangGraph Editor</h1>
                <div class="instructions">
                    <h2>To run the React Editor:</h2>
                    <ol>
                        <li>Navigate to the React editor directory:<br>
                            <code>cd /root/qwen/ai_agent/gui/react_editor</code></li>
                        <li>Install dependencies:<br>
                            <code>npm install</code></li>
                        <li>Start the development server:<br>
                            <code>npx create-react-app . --template && npm start</code></li>
                        <li>Or if you already have create-react-app set up:<br>
                            <code>npm start</code></li>
                    </ol>
                    <p>Then access the React editor at <a href="http://localhost:3000" target="_blank">http://localhost:3000</a></p>
                </div>
            </body>
            </html>
            '''
            self.wfile.write(react_info.encode())
            return
        elif self.path == '/docs/integration-guide':
            self.path = '/LANGGRAPH_STUDIO_INTEGRATION.md'

        return super().do_GET()

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

def run_streamlit_app():
    """Run the Streamlit app in a separate thread."""
    import subprocess
    subprocess.Popen([
        "streamlit", "run", 
        str(Path(__file__).parent / "enhanced_streamlit_app.py"),
        "--server.port", "8501",
        "--server.headless", "true"
    ])

def main():
    port = 8000
    server_address = ('', port)
    
    # Start Streamlit in background
    print("Starting Streamlit app...")
    run_streamlit_app()
    
    # Start the main server
    httpd = HTTPServer(server_address, LangGraphEditorServer)
    print(f"LangGraph Visual Editor Suite running at http://localhost:{port}")
    print("Available interfaces:")
    print("- Main dashboard: http://localhost:8000")
    print("- Streamlit editor: http://localhost:8501")
    print("Press Ctrl+C to stop the server")
    
    # Open the main page in the browser
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        httpd.shutdown()

if __name__ == "__main__":
    main()