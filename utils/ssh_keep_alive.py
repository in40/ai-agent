"""
Utility module to keep SSH sessions alive during long-running operations like LLM requests.
"""
import threading
import time
import signal
import sys
import os
import logging

logger = logging.getLogger(__name__)

class SSHKeepAlive:
    """
    A utility class to keep SSH sessions alive during long-running operations.
    
    This class sends periodic signals to the terminal to prevent the SSH session
    from timing out due to inactivity during long-running operations like LLM requests.
    """
    
    def __init__(self, interval=60):
        """
        Initialize the SSHKeepAlive utility.
        
        Args:
            interval (int): Interval in seconds between keep-alive signals. Default is 60 seconds.
        """
        self.interval = interval
        self._timer_thread = None
        self._stop_event = threading.Event()
        self._is_active = False
        
    def _keep_alive_worker(self):
        """
        Worker function that runs in a separate thread to send keep-alive signals.
        """
        while not self._stop_event.wait(self.interval):
            try:
                # Send a null byte to the terminal to keep the session alive
                # This is equivalent to pressing Ctrl+@ in some terminals
                if os.isatty(sys.stdout.fileno()):
                    sys.stdout.write('\x00')  # Null byte
                    sys.stdout.flush()
                
                # Also update the SSH client's last activity timestamp if possible
                # This works with OpenSSH clients that support the escape sequence
                if os.environ.get('SSH_CLIENT'):
                    # Try to send a no-op command to the SSH client
                    # This is just for logging purposes
                    logger.debug("SSH keep-alive signal sent")
                    
            except Exception as e:
                logger.warning(f"Error sending keep-alive signal: {e}")
                
    def start(self):
        """
        Start the keep-alive mechanism.
        """
        if self._is_active:
            logger.warning("SSHKeepAlive is already active")
            return
            
        # Check if we're running in an SSH session
        if not os.environ.get('SSH_CLIENT') and not os.environ.get('SSH_TTY'):
            logger.info("Not running in an SSH session, keep-alive not needed")
            return
            
        self._is_active = True
        self._stop_event.clear()
        self._timer_thread = threading.Thread(target=self._keep_alive_worker, daemon=True)
        self._timer_thread.start()
        logger.info(f"SSH keep-alive started with {self.interval}s interval")
        
    def stop(self):
        """
        Stop the keep-alive mechanism.
        """
        if not self._is_active:
            return
            
        self._is_active = False
        self._stop_event.set()
        if self._timer_thread and self._timer_thread.is_alive():
            self._timer_thread.join(timeout=2)  # Wait up to 2 seconds for thread to finish
        logger.info("SSH keep-alive stopped")
        
    def __enter__(self):
        """
        Context manager entry.
        """
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Context manager exit.
        """
        self.stop()


def keep_ssh_alive_for_llm_call(func, *args, **kwargs):
    """
    Decorator-like function that wraps an LLM call with SSH keep-alive functionality.
    
    Args:
        func: The function to call (typically an LLM request)
        *args: Arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function
        
    Returns:
        Result of the function call
    """
    with SSHKeepAlive(interval=45):  # Use slightly shorter interval for LLM calls
        return func(*args, **kwargs)


class SSHKeepAliveContext:
    """
    Context manager for keeping SSH alive during specific code blocks.
    
    Example usage:
        with SSHKeepAliveContext():
            # Long-running operation here
            result = llm_client.generate(prompt)
    """
    
    def __init__(self, interval=60):
        self.keep_alive = SSHKeepAlive(interval)
        
    def __enter__(self):
        self.keep_alive.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.keep_alive.stop()


# Global instance for convenience
ssh_keep_alive = SSHKeepAlive(interval=60)