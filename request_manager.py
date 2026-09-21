"""
Request Manager for Jarvis - Centralized request lifecycle management.
Handles unique request IDs, state tracking, cancellation, and duplicate prevention.
"""

import threading
import time
import uuid
from typing import Optional, Dict, Any


class RequestState:
    """Enum-like class for request states."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SEARCHING = "searching"
    RESPONSE_READY = "response_ready"
    CHAT_UPDATED = "chat_updated"
    SPEAKING = "speaking"
    ERROR = "error"
    CANCELLED = "cancelled"


class RequestEvent:
    """Represents a lifecycle event for a request."""
    
    REQUEST_STARTED = "REQUEST_STARTED"
    STATE_CHANGED = "STATE_CHANGED"
    LOCATION_LOOKUP_STARTED = "LOCATION_LOOKUP_STARTED"
    SEARCH_STARTED = "SEARCH_STARTED"
    RESPONSE_READY = "RESPONSE_READY"
    CHAT_UPDATED = "CHAT_UPDATED"
    TTS_STARTED = "TTS_STARTED"
    TTS_FINISHED = "TTS_FINISHED"
    REQUEST_CANCELLED = "REQUEST_CANCELLED"
    REQUEST_FAILED = "REQUEST_FAILED"
    REQUEST_COMPLETED = "REQUEST_COMPLETED"


class Request:
    """Represents a single user request with its lifecycle."""
    
    def __init__(self, request_id: str, source: str = "unknown"):
        self.id = request_id
        self.source = source  # "voice", "text", etc.
        self.state = RequestState.IDLE
        self.cancelled = False
        self.cancellation_event = threading.Event()
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.response_text: Optional[str] = None
        self.error_message: Optional[str] = None
        
        # Track operations to prevent duplicates
        self.operations_started: Dict[str, bool] = {}
        
        # Event history for logging/debugging
        self.events: list = []
    
    def cancel(self):
        """Mark this request as cancelled."""
        if not self.cancelled:
            self.cancelled = True
            self.cancellation_event.set()
            self._log_event(RequestEvent.REQUEST_CANCELLED, "Request marked as cancelled")
    
    def is_cancelled(self) -> bool:
        """Check if request has been cancelled."""
        return self.cancelled
    
    def wait_for_cancellation(self, timeout: Optional[float] = None):
        """Block until cancellation or timeout."""
        return self.cancellation_event.wait(timeout=timeout)
    
    def start_operation(self, operation_name: str) -> bool:
        """
        Mark an operation as started. Returns False if already started (duplicate).
        """
        if operation_name in self.operations_started:
            return False  # Duplicate
        
        self.operations_started[operation_name] = True
        return True
    
    def set_state(self, new_state: str):
        """Update request state."""
        old_state = self.state
        self.state = new_state
        if new_state in [RequestState.IDLE, RequestState.ERROR, RequestState.CANCELLED]:
            self.completed_at = time.time()
    
    def _log_event(self, event_type: str, details: str = ""):
        """Log a lifecycle event."""
        self.events.append({
            "timestamp": time.time(),
            "event": event_type,
            "state": self.state,
            "cancelled": self.cancelled,
            "details": details
        })


class RequestManager:
    """
    Manages the lifecycle of all requests. Thread-safe.
    
    Ensures:
    - Unique request IDs
    - Only one active request at a time (or tracks multiple if needed)
    - Proper state transitions
    - Cancellation support
    - Duplicate prevention
    """
    
    def __init__(self):
        self._lock = threading.Lock()
        self.active_request: Optional[Request] = None
        self.request_history: list = []
        self._request_counter = 0
    
    def create_request(self, source: str = "unknown") -> Request:
        """Create a new request and set it as active."""
        with self._lock:
            self._request_counter += 1
            request_id = f"req-{self._request_counter}-{uuid.uuid4().hex[:8]}"
            
            # If there's an existing active request, complete/cancel it
            if self.active_request and not self.active_request.completed_at:
                print(f"[RequestManager] Previous request {self.active_request.id} "
                      f"superseded by new request")
                self.active_request.cancel()
            
            request = Request(request_id, source)
            request.set_state(RequestState.PROCESSING)
            self.active_request = request
            
            return request
    
    def get_active_request(self) -> Optional[Request]:
        """Get the currently active request."""
        with self._lock:
            return self.active_request
    
    def is_current_request(self, request_id: str) -> bool:
        """Check if a given request ID is still the active one."""
        with self._lock:
            return (self.active_request is not None and 
                    self.active_request.id == request_id and
                    not self.active_request.cancelled)
    
    def cancel_active(self) -> Optional[Request]:
        """Cancel the currently active request."""
        with self._lock:
            if self.active_request and not self.active_request.completed_at:
                self.active_request.cancel()
                return self.active_request
            return None
    
    def complete_request(self, request_id: str, response_text: Optional[str] = None):
        """Mark a request as completed."""
        with self._lock:
            if (self.active_request and 
                self.active_request.id == request_id and
                not self.active_request.completed_at):
                
                self.active_request.response_text = response_text
                self.active_request.set_state(RequestState.IDLE)
                self.request_history.append(self.active_request)
    
    def fail_request(self, request_id: str, error_message: str):
        """Mark a request as failed."""
        with self._lock:
            if (self.active_request and 
                self.active_request.id == request_id and
                not self.active_request.completed_at):
                
                self.active_request.error_message = error_message
                self.active_request.set_state(RequestState.ERROR)
                self.request_history.append(self.active_request)
    
    def log_event(self, request_id: str, event_type: str, details: str = ""):
        """Log an event for a specific request."""
        with self._lock:
            if self.active_request and self.active_request.id == request_id:
                self.active_request._log_event(event_type, details)
