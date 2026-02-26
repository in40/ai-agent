"""
STDIO Transport for MCP Server
Implements the standard STDIO transport as per MCP specification
"""
import sys
import threading
from typing import Callable, Optional
from ..utils.json_rpc import JsonRpcHandler, JsonRpcMessage


class StdioTransport:
    """Transport mechanism using STDIO as per MCP specification"""

    def __init__(self, rpc_handler: JsonRpcHandler):
        self.rpc_handler = rpc_handler
        self.running = False
        self.reader_thread: Optional[threading.Thread] = None
        self.message_callback: Optional[Callable[[JsonRpcMessage], None]] = None
        self.stdin_lock = threading.Lock()
        self.stdout_lock = threading.Lock()

    def start(self, message_callback: Callable[[JsonRpcMessage], None]):
        """Start the STDIO transport server"""
        self.message_callback = message_callback
        self.running = True

        # Start a thread to read from stdin
        self.reader_thread = threading.Thread(target=self._read_stdin, daemon=True)
        self.reader_thread.start()

    def stop(self):
        """Stop the STDIO transport server"""
        self.running = False
        if self.reader_thread and self.reader_thread.is_alive():
            self.reader_thread.join(timeout=1.0)

    def _read_stdin(self):
        """Read messages from stdin and process them"""
        try:
            while self.running:
                line = sys.stdin.readline()
                if not line:
                    # EOF reached, exit the loop
                    break
                
                line = line.strip()
                if not line:
                    continue
                
                try:
                    # Parse the message
                    message = self.rpc_handler.parse_message(line)
                    
                    # Process the message using the callback
                    if self.message_callback:
                        self.message_callback(message)
                        
                except Exception as e:
                    # Send error message to stderr
                    error_msg = f"Error processing message: {str(e)}"
                    self.send_error(error_msg)
                    
        except Exception as e:
            self.send_error(f"Error reading from stdin: {str(e)}")

    def send_message(self, message: JsonRpcMessage):
        """Send a message to stdout"""
        if not self.running:
            return
            
        try:
            msg_str = message.to_json()
            with self.stdout_lock:
                print(msg_str, flush=True)
        except Exception as e:
            self.send_error(f"Error sending message: {str(e)}")

    def send_error(self, error_msg: str):
        """Send an error message to stderr"""
        try:
            print(f"[STDIO Transport Error] {error_msg}", file=sys.stderr, flush=True)
        except Exception:
            # If we can't even write to stderr, there's nothing we can do
            pass