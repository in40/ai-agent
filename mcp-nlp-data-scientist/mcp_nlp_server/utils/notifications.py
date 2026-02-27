"""
Notifications Manager for MCP Server
Manages MCP notifications for dynamic updates
"""
from typing import Dict, Any, Callable, List
from ..utils.json_rpc import JsonRpcHandler, JsonRpcMessage


class NotificationManager:
    """Manages MCP notifications for dynamic updates"""

    def __init__(self, rpc_handler: JsonRpcHandler):
        self.rpc_handler = rpc_handler
        self.notification_callbacks: Dict[str, List[Callable]] = {
            "notifications/tools/list_changed": [],
            "notifications/resources/list_changed": [],
            "notifications/prompts/list_changed": [],
        }
        self.changes_status = {
            "tools_changed": False,
            "resources_changed": False,
            "prompts_changed": False,
        }

    def register_handlers(self, rpc_handler: JsonRpcHandler):
        """Register notification-related handlers"""
        # No request handlers needed for notifications, they are server-initiated
        pass

    def register_notification_callback(self, method: str, callback: Callable):
        """Register a callback for a specific notification method"""
        if method not in self.notification_callbacks:
            self.notification_callbacks[method] = []
        self.notification_callbacks[method].append(callback)

    def notify_tools_list_changed(self):
        """Notify that the tools list has changed"""
        notification = JsonRpcMessage(
            message_type="notification",  # Using string as MessageType is not imported here
            method="notifications/tools/list_changed",
            params={}
        )
        
        # Call registered callbacks
        for callback in self.notification_callbacks.get("notifications/tools/list_changed", []):
            callback(notification)
        
        # Reset the change flag
        self.changes_status["tools_changed"] = False

    def notify_resources_list_changed(self):
        """Notify that the resources list has changed"""
        notification = JsonRpcMessage(
            message_type="notification",
            method="notifications/resources/list_changed",
            params={}
        )
        
        # Call registered callbacks
        for callback in self.notification_callbacks.get("notifications/resources/list_changed", []):
            callback(notification)
        
        # Reset the change flag
        self.changes_status["resources_changed"] = False

    def notify_prompts_list_changed(self):
        """Notify that the prompts list has changed"""
        notification = JsonRpcMessage(
            message_type="notification",
            method="notifications/prompts/list_changed",
            params={}
        )
        
        # Call registered callbacks
        for callback in self.notification_callbacks.get("notifications/prompts/list_changed", []):
            callback(notification)
        
        # Reset the change flag
        self.changes_status["prompts_changed"] = False

    def mark_tools_changed(self):
        """Mark that tools have changed"""
        self.changes_status["tools_changed"] = True

    def mark_resources_changed(self):
        """Mark that resources have changed"""
        self.changes_status["resources_changed"] = True

    def mark_prompts_changed(self):
        """Mark that prompts have changed"""
        self.changes_status["prompts_changed"] = True

    def get_changes_status(self) -> Dict[str, bool]:
        """Get the current changes status"""
        return self.changes_status.copy()