"""
Status Panel - Displays current Jarvis state, recent activity, and system info.
Includes location display with graceful loading/missing/error states.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtCore import Qt


class StatusPanel(QWidget):
    """Futuristic status panel showing current state, messages, and system info."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)
        
        # State label
        self.state_label = QLabel("STATE: IDLE")
        self.state_label.setStyleSheet("""
            color: #00ff88;
            font-family: 'Consolas', monospace;
            font-size: 12px;
            letter-spacing: 1px;
        """)
        layout.addWidget(self.state_label)
        
        # Message label
        self.message_label = QLabel("JARVIS is ready.")
        self.message_label.setStyleSheet("""
            color: rgba(0, 255, 255, 0.8);
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
        """)
        layout.addWidget(self.message_label)
        
        # Activity log (last few actions with timestamps)
        self.activity_label = QLabel("")
        self.activity_label.setStyleSheet("""
            color: rgba(255, 255, 255, 0.4);
            font-family: 'Consolas', monospace;
            font-size: 9px;
        """)
        layout.addWidget(self.activity_label)
        
        self.activity_history = []
    
    def update_status(self, state, message):
        """Update the status panel with new state and message."""
        # Update state label with color based on state
        colors = {
            "idle": "#00ff88",
            "listening": "#00ffff",
            "processing": "#ffaa00",
            "speaking": "#ff4488",
            "error": "#ff4444"
        }
        
        color = colors.get(state, "#ffffff")
        self.state_label.setText(f"STATE: {state.upper()}")
        self.state_label.setStyleSheet(f"""
            color: {color};
            font-family: 'Consolas', monospace;
            font-size: 12px;
            letter-spacing: 1px;
        """)
        
        # Update message
        self.message_label.setText(message)
        
        # Add to activity history with timestamp
        import time
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {state}: {message[:50]}"
        self.activity_history.append(entry)
        
        # Keep only last 3 entries
        if len(self.activity_history) > 3:
            self.activity_history.pop(0)
        
        self.activity_label.setText("\n".join(self.activity_history[-3:]))
    
    def update_location(self, location_data):
        """Add location info to the activity log with timestamp.
        
        Args:
            location_data: Dict with keys city, region, country, lat, lon, timezone
                          or None if unavailable.
        """
        if not location_data:
            return
        
        # Format as simple location string
        city = location_data.get("city", "")
        region = location_data.get("region", "")
        country = location_data.get("country", "")
        
        parts = []
        if city:
            parts.append(city)
        if region:
            parts.append(region)
        if country:
            parts.append(country)
        
        if parts:
            loc_str = ", ".join(parts)
            
            # Add to activity history with timestamp (matching screenshot format)
            import time
            timestamp = time.strftime("%H:%M:%S")
            entry = f"[{timestamp}] location: {loc_str}"
            self.activity_history.append(entry)
            
            # Keep only last 3 entries
            if len(self.activity_history) > 3:
                self.activity_history.pop(0)
            
            self.activity_label.setText("\n".join(self.activity_history[-3:]))