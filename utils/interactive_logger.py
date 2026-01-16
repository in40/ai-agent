"""
Interactive Logger Utility - Provides dynamic logging control for interactive applications
to suppress heartbeat and other background logs during user interaction.
"""

import logging
import threading
import sys
from typing import Optional


class InteractiveLogger:
    """
    A logging utility that can dynamically suppress certain types of logs
    during user interaction to prevent interference with the user experience.
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self._suppress_heartbeats = False
        self._original_filters = {}
        
        # Initialize heartbeat filter
        self._heartbeat_filter = HeartbeatFilter()
        
        # Store original filters for restoration
        self._store_original_filters()
    
    def _store_original_filters(self):
        """Store original filters for all loggers to restore later."""
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            self._original_filters[logger_name] = list(logger.filters)
    
    def suppress_heartbeats(self):
        """Enable suppression of heartbeat messages."""
        with self._lock:
            # Only apply suppression if INTERACTIVE_MODE is enabled
            import os
            if os.getenv("INTERACTIVE_MODE", "").lower() in ("true", "1", "yes"):
                if not self._suppress_heartbeats:
                    self._apply_heartbeat_filter()
                    self._suppress_heartbeats = True
            # If interactive mode is not enabled, do nothing

    def show_heartbeats(self):
        """Disable suppression of heartbeat messages."""
        with self._lock:
            if self._suppress_heartbeats:
                self._remove_heartbeat_filter()
                self._suppress_heartbeats = False
    
    def _apply_heartbeat_filter(self):
        """Apply heartbeat filter to relevant loggers."""
        # Apply to root logger
        root_logger = logging.getLogger()
        if self._heartbeat_filter not in root_logger.filters:
            root_logger.addFilter(self._heartbeat_filter)
        
        # Apply to specific loggers that might emit heartbeat messages
        for logger_name in ['service_registry', 'registry_client', 'MCPServer']:
            logger = logging.getLogger(logger_name)
            if self._heartbeat_filter not in logger.filters:
                logger.addFilter(self._heartbeat_filter)
    
    def _remove_heartbeat_filter(self):
        """Remove heartbeat filter from relevant loggers."""
        # Remove from root logger
        root_logger = logging.getLogger()
        if self._heartbeat_filter in root_logger.filters:
            root_logger.removeFilter(self._heartbeat_filter)
        
        # Remove from specific loggers
        for logger_name in ['service_registry', 'registry_client', 'MCPServer']:
            logger = logging.getLogger(logger_name)
            if self._heartbeat_filter in logger.filters:
                logger.removeFilter(self._heartbeat_filter)


class HeartbeatFilter(logging.Filter):
    """Custom filter to suppress heartbeat messages."""

    def filter(self, record):
        # Suppress heartbeat-related messages
        message = record.getMessage()
        if ("Heartbeat received for service" in message or 
            "HTTP \"PUT /heartbeat" in message or
            "Heartbeat sent for service" in message):
            return False
        return True


# Global instance
interactive_logger = InteractiveLogger()


def setup_interactive_logging():
    """
    Set up logging configuration that respects the interactive mode.
    """
    # Configure root logger
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # Ensure logs go to stdout
        ]
    )


def suppress_heartbeats():
    """Suppress heartbeat messages."""
    interactive_logger.suppress_heartbeats()


def show_heartbeats():
    """Show heartbeat messages."""
    interactive_logger.show_heartbeats()