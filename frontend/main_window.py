"""
Futuristic Jarvis Frontend - Main Application Window
PyQt6-based UI with circular HUD, waveform visualizer, and chat interface.
Primary interaction through frontend chat and voice (Listen button).
"""

import sys
import os
import threading
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QFrame, QGraphicsDropShadowEffect,
    QTextEdit, QLineEdit, QTabWidget, QScrollArea, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPainter, QPen, QBrush

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from frontend.hud_widget import CircularHUD
from frontend.waveform_visualizer import WaveformVisualizer
from frontend.status_panel import StatusPanel


class JarvisSignals(QObject):
    """Signal emitter for Jarvis state changes."""
    state_changed = pyqtSignal(str, str)  # state, message
    waveform_data = pyqtSignal(list)      # amplitude values for visualizer
    chat_message_received = pyqtSignal(str, str, bool)  # sender, text, is_user


class ChatMessageWidget(QWidget):
    """A single chat message widget with futuristic HUD styling."""
    
    def __init__(self, sender, text, is_user=False):
        super().__init__()
        self.sender = sender
        self.text = text
        self.is_user = is_user
        
        # Main container with border
        self.setStyleSheet("""
            ChatMessageWidget {
                background-color: rgba(10, 20, 40, 0.6);
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 8px;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(4)
        
        # Sender label (uppercase, small, teal accent)
        sender_label = QLabel(sender.upper())
        sender_font = QFont('Segoe UI', 9, QFont.Weight.Bold)
        sender_label.setFont(sender_font)
        if is_user:
            sender_label.setStyleSheet("""
                color: #88ccff;
                letter-spacing: 1px;
                font-size: 9px;
            """)
        else:
            sender_label.setStyleSheet("""
                color: #00ffff;
                letter-spacing: 1px;
                font-size: 9px;
            """)
        layout.addWidget(sender_label)
        
        # Separator line
        separator = QFrame()
        separator.setFixedHeight(1)
        if is_user:
            separator.setStyleSheet("background-color: rgba(136, 204, 255, 0.3);")
        else:
            separator.setStyleSheet("background-color: rgba(0, 255, 255, 0.3);")
        layout.addWidget(separator)
        
        # Message text
        msg_label = QLabel(text)
        msg_font = QFont('Segoe UI', 10)
        msg_label.setFont(msg_font)
        msg_label.setWordWrap(True)
        if is_user:
            msg_label.setStyleSheet("""
                color: #ffffff;
                font-size: 10px;
            """)
        else:
            msg_label.setStyleSheet("""
                color: #cccccc;
                font-size: 10px;
            """)
        layout.addWidget(msg_label)


class JarvisFrontend(QMainWindow):
    """Main futuristic frontend window for Jarvis assistant."""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("JARVIS - Just A Rather Very Intelligent System")
        self.setFixedSize(1200, 800)
        self.setStyleSheet(self.get_main_stylesheet())
        
        # Initialize Jarvis backend (includes location detection during init)
        try:
            from jarvis import JarvisAssistant
            self.jarvis = JarvisAssistant()
            print("Jarvis backend initialized successfully.")
        except Exception as e:
            print(f"Warning: Could not initialize Jarvis backend: {e}")
            self.jarvis = None
        
        # Signal emitter for UI updates - must be created on main thread
        self.signals = JarvisSignals()
        self.signals.state_changed.connect(self.update_state)
        self.signals.chat_message_received.connect(self.add_chat_message)
        
        # State machine with thread-safe transitions
        self.current_state = "idle"
        self.state_lock = threading.Lock()
        self.is_listening = False
        
        # Request tracking for response ordering (now uses RequestManager)
        self.active_request_id = None
        
        # Track active threads for proper cancellation and waiting
        self.listen_thread = None
        self.process_thread = None
        self.chat_processing = False
        
        self.conversation_history = []
        
        # Build the UI
        self.setup_ui()
        
        # Update location display in status panel after backend init
        if self.jarvis:
            QTimer.singleShot(100, lambda: self.status_panel.update_location(self.jarvis.location_data))
        
        # Start with idle animation
        QTimer.singleShot(200, lambda: self.signals.state_changed.emit("idle", "JARVIS is now active."))
    
    def get_main_stylesheet(self):
        """Return the main application stylesheet."""
        return """
            QMainWindow {
                background-color: #0a0e17;
            }
            
            QWidget#centralWidget {
                background-color: #0a0e17;
            }
            
            QPushButton {
                background-color: rgba(0, 255, 255, 0.1);
                border: 1px solid rgba(0, 255, 255, 0.3);
                color: #00ffff;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.2);
                border: 1px solid rgba(0, 255, 255, 0.6);
            }
            
            QPushButton:pressed {
                background-color: rgba(0, 255, 255, 0.3);
            }
        """
    
    def setup_ui(self):
        """Build the futuristic UI layout with chat as primary interface."""
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Top section: Title and status
        top_section = QHBoxLayout()
        
        title_label = QLabel("JARVIS")
        title_font = QFont('Segoe UI', 24, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #00ffff;
            font-weight: bold;
            letter-spacing: 4px;
        """)
        top_section.addWidget(title_label)
        
        top_section.addStretch()
        
        # Status indicator light
        self.status_light = QLabel("")
        self.status_light.setFixedSize(12, 12)
        self.status_light.setStyleSheet("""
            background-color: #00ff88;
            border-radius: 6px;
        """)
        top_section.addWidget(self.status_light)
        
        self.status_label = QLabel("ONLINE")
        self.status_label.setStyleSheet("""
            color: #00ff88;
            font-family: 'Consolas', monospace;
            font-size: 11px;
            letter-spacing: 2px;
        """)
        top_section.addWidget(self.status_label)
        
        main_layout.addLayout(top_section)
        
        # Middle section: HUD + Chat/Terminal tabs
        middle_section = QHBoxLayout()
        middle_section.setSpacing(15)
        
        # Left: Circular HUD (30% width)
        hud_container = QFrame()
        hud_container.setStyleSheet("""
            background-color: rgba(10, 20, 40, 0.8);
            border: 1px solid rgba(0, 255, 255, 0.2);
            border-radius: 10px;
        """)
        hud_layout = QVBoxLayout(hud_container)
        hud_layout.setContentsMargins(10, 10, 10, 10)
        
        self.hud = CircularHUD()
        hud_layout.addWidget(self.hud)
        
        # Waveform below HUD
        waveform_title = QLabel("AUDIO INPUT")
        waveform_title.setStyleSheet("""
            color: rgba(0, 255, 255, 0.7);
            font-family: 'Consolas', monospace;
            font-size: 10px;
            letter-spacing: 2px;
        """)
        hud_layout.addWidget(waveform_title)
        
        self.waveform = WaveformVisualizer()
        hud_layout.addWidget(self.waveform)
        
        middle_section.addWidget(hud_container, stretch=3)
        
        # Right: Tabbed interface (Chat primary, API settings secondary)
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 10px;
                background-color: rgba(10, 20, 40, 0.8);
            }
            QTabBar::tab {
                background-color: rgba(0, 255, 255, 0.1);
                border: 1px solid rgba(0, 255, 255, 0.3);
                color: #00ffff;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
            }
            QTabBar::tab:selected {
                background-color: rgba(0, 255, 255, 0.3);
                border-bottom: none;
            }
        """)
        
        # Chat tab (primary)
        chat_tab = self.create_chat_tab()
        self.tabs.addTab(chat_tab, "Chat")
        
        # Edit Local API tab
        api_tab = self.create_api_settings_tab()
        self.tabs.addTab(api_tab, "Edit Local API")
        
        middle_section.addWidget(self.tabs, stretch=7)
        
        main_layout.addLayout(middle_section, stretch=1)
        
        # Bottom section: Status panel and controls
        bottom_section = QHBoxLayout()
        
        self.status_panel = StatusPanel()
        bottom_section.addWidget(self.status_panel, stretch=1)
        
        # Control buttons
        controls_frame = QFrame()
        controls_layout = QVBoxLayout(controls_frame)
        
        listen_btn = QPushButton("LISTEN")
        listen_btn.clicked.connect(self.toggle_listening)
        self.listen_button = listen_btn
        controls_layout.addWidget(listen_btn)
        
        exit_btn = QPushButton("EXIT")
        exit_btn.clicked.connect(self.close)
        controls_layout.addWidget(exit_btn)
        
        bottom_section.addWidget(controls_frame)
        
        main_layout.addLayout(bottom_section)
    
    def create_chat_tab(self):
        """Create the chat interface tab."""
        chat_widget = QWidget()
        layout = QVBoxLayout(chat_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Chat messages area (scrollable) - dark navy background with teal border
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setStyleSheet("""
            QScrollArea {
                background-color: rgba(5, 10, 20, 0.95);
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 8px;
            }
            QScrollBar:vertical {
                background-color: rgba(10, 20, 40, 0.5);
                width: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(0, 255, 255, 0.3);
                border-radius: 4px;
                min-height: 20px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        self.chat_messages_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_messages_container)
        self.chat_layout.setContentsMargins(12, 12, 12, 12)
        self.chat_layout.setSpacing(8)
        self.chat_layout.addStretch()
        
        self.chat_scroll.setWidget(self.chat_messages_container)
        self.chat_scroll.setWidgetResizable(True)
        layout.addWidget(self.chat_scroll, stretch=1)
        
        # Input area with Stop Chat button - futuristic styling
        input_frame = QFrame()
        input_layout = QHBoxLayout(input_frame)
        input_layout.setContentsMargins(5, 5, 5, 5)
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Type your message to JARVIS...")
        self.chat_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(10, 20, 40, 0.9);
                border: 1px solid rgba(0, 255, 255, 0.3);
                border-radius: 8px;
                color: #ffffff;
                padding: 10px;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit:focus {
                border: 1px solid rgba(0, 255, 255, 0.6);
            }
        """)
        self.chat_input.returnPressed.connect(self.send_chat_message)
        input_layout.addWidget(self.chat_input, stretch=1)
        
        ask_btn = QPushButton("Ask Jarvis")
        ask_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(0, 255, 255, 0.1);
                border: 1px solid rgba(0, 255, 255, 0.3);
                color: #00ffff;
                padding: 8px 16px;
                font-family: 'Segoe UI', sans-serif;
            }
            QPushButton:hover {
                background-color: rgba(0, 255, 255, 0.2);
                border: 1px solid rgba(0, 255, 255, 0.6);
            }
        """)
        ask_btn.clicked.connect(self.send_chat_message)
        input_layout.addWidget(ask_btn)
        
        # Stop Chat button (initially hidden) - now serves as Cancel/Stop button
        self.stop_chat_button = QPushButton("Stop")
        self.stop_chat_button.setStyleSheet("""
            background-color: rgba(255, 68, 68, 0.1);
            border: 1px solid rgba(255, 68, 68, 0.3);
            color: #ff4444;
        """)
        self.stop_chat_button.clicked.connect(self.cancel_active_request)
        self.stop_chat_button.hide()
        input_layout.addWidget(self.stop_chat_button)
        
        layout.addWidget(input_frame)
        
        # Add initial welcome message
        self.add_chat_message("JARVIS", "Good day, Sir. How may I assist you?", is_user=False)
        
        # Play startup greeting after a short delay to ensure audio system is ready
        QTimer.singleShot(500, self.play_startup_greeting)
        
        return chat_widget
    
    def create_api_settings_tab(self):
        """Create the Edit Local API settings tab."""
        api_widget = QWidget()
        layout = QVBoxLayout(api_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Edit Local API")
        title_font = QFont('Segoe UI', 16, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_label.setStyleSheet("""
            color: #00ffff;
            letter-spacing: 2px;
        """)
        layout.addWidget(title_label)
        
        # Description
        desc_label = QLabel("Configure the LM Studio API endpoint.")
        desc_label.setStyleSheet("""
            color: rgba(0, 255, 255, 0.7);
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
        """)
        layout.addWidget(desc_label)
        
        # API URL field
        url_frame = QFrame()
        url_layout = QVBoxLayout(url_frame)
        url_layout.setContentsMargins(0, 0, 0, 0)
        
        url_title = QLabel("API URL")
        url_title.setStyleSheet("""
            color: rgba(0, 255, 255, 0.8);
            font-family: 'Consolas', monospace;
            font-size: 11px;
            letter-spacing: 1px;
        """)
        url_layout.addWidget(url_title)
        
        self.api_url_input = QLineEdit()
        # Load current API URL from config or use default
        if self.jarvis and hasattr(self.jarvis, 'config'):
            self.api_url_input.setText(self.jarvis.config.get("lm_studio", {}).get("api_base", "http://localhost:1234/v1"))
        else:
            self.api_url_input.setText("http://localhost:1234/v1")
        
        self.api_url_input.setStyleSheet("""
            background-color: rgba(10, 20, 40, 0.9);
            border: 1px solid rgba(0, 255, 255, 0.3);
            border-radius: 8px;
            color: #ffffff;
            padding: 10px;
            font-family: 'Consolas', monospace;
        """)
        url_layout.addWidget(self.api_url_input)
        
        layout.addWidget(url_frame)
        
        # Save button and status message
        save_frame = QFrame()
        save_layout = QHBoxLayout(save_frame)
        save_layout.setContentsMargins(0, 0, 0, 0)
        
        self.save_api_btn = QPushButton("Save")
        self.save_api_btn.clicked.connect(self.save_api_settings)
        save_layout.addWidget(self.save_api_btn)
        
        layout.addWidget(save_frame)
        
        # Status message area
        self.api_status_label = QLabel("")
        self.api_status_label.setStyleSheet("""
            color: #00ff88;
            font-family: 'Segoe UI', sans-serif;
            font-size: 11px;
        """)
        layout.addWidget(self.api_status_label)
        
        return api_widget
    
    def save_api_settings(self):
        """Save the API URL settings."""
        url = self.api_url_input.text().strip()
        
        # Basic URL validation
        if not url:
            self.show_api_status("Error: URL cannot be empty.", error=True)
            return
        
        if not (url.startswith("http://") or url.startswith("https://")):
            self.show_api_status("Error: URL must start with http:// or https://", error=True)
            return
        
        # Save to config file
        try:
            import json
            
            config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.json")
            
            # Load existing config
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update API URL
            if "lm_studio" not in config:
                config["lm_studio"] = {}
            config["lm_studio"]["api_base"] = url
            
            # Save config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            self.show_api_status("API URL saved successfully.")
            
        except Exception as e:
            self.show_api_status(f"Error saving API URL: {str(e)}", error=True)
    
    def show_api_status(self, message, error=False):
        """Show status message in the API settings tab."""
        self.api_status_label.setText(message)
        if error:
            self.api_status_label.setStyleSheet("""
                color: #ff4444;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            """)
        else:
            self.api_status_label.setStyleSheet("""
                color: #00ff88;
                font-family: 'Segoe UI', sans-serif;
                font-size: 11px;
            """)
    
    def play_startup_greeting(self):
        """Play the startup greeting using cached audio if available."""
        try:
            if self.jarvis and hasattr(self.jarvis, 'speak_startup_greeting'):
                # Run in separate thread to avoid blocking UI
                threading.Thread(target=self.jarvis.speak_startup_greeting, daemon=True).start()
        except Exception as e:
            print(f"Error playing startup greeting: {e}")

    def add_chat_message(self, sender, text, is_user=False):
        """Add a message to the chat interface (thread-safe via signal)."""
        # Use QTimer.singleShot to ensure we're on the main thread
        QTimer.singleShot(0, lambda s=sender, t=text, u=is_user: self._add_chat_message_internal(s, t, u))

    def _add_chat_message_internal(self, sender, text, is_user=False):
        """Internal method to add chat message (must be called on main thread)."""
        msg_widget = ChatMessageWidget(sender, text, is_user=is_user)
        # Remove stretch, add message, re-add stretch
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count() - 1))
        self.chat_layout.addWidget(msg_widget)
        self.chat_layout.addStretch()
        
        # Scroll to bottom
        QTimer.singleShot(50, lambda: self.chat_scroll.verticalScrollBar().setValue(
            self.chat_scroll.verticalScrollBar().maximum()))
    
    def set_state(self, state, message):
        """Thread-safe state transition with validation."""
        valid_states = ["idle", "listening", "processing", "searching", 
                       "response_ready", "chat_updated", "speaking", "error"]
        if state not in valid_states:
            print(f"Warning: Invalid state '{state}'")
            return
        
        # Validate transitions to prevent race conditions
        allowed_transitions = {
            "idle": ["listening", "processing"],
            "listening": ["processing", "speaking", "error", "idle"],
            "processing": ["searching", "response_ready", "error", "idle"],
            "searching": ["response_ready", "error", "idle"],
            "response_ready": ["chat_updated", "error"],
            "chat_updated": ["speaking", "idle"],
            "speaking": ["idle", "error"],
            "error": ["idle"]
        }
        
        with self.state_lock:
            if state != self.current_state and state not in allowed_transitions.get(self.current_state, []):
                print(f"Warning: Invalid transition {self.current_state} -> {state}")
            
            self.current_state = state
        
        # Emit signal to update UI on main thread
        QTimer.singleShot(0, lambda s=state, m=message: self.signals.state_changed.emit(s, m))

    def get_state(self):
        """Get current state (thread-safe)."""
        with self.state_lock:
            return self.current_state

    def next_request_id(self):
        """Generate a new unique request ID via RequestManager."""
        if not self.jarvis:
            return None
        
        request = self.jarvis.request_manager.create_request(source="text")
        self.active_request_id = request.id
        return request.id

    def is_current_request(self, request_id):
        """Check if this request ID is still the active one (not superseded)."""
        if not self.jarvis:
            return False
        
        return self.jarvis.request_manager.is_current_request(request_id)

    def cancel_active_request(self):
        """Cancel the currently active request."""
        if not self.jarvis:
            return None
        
        cancelled = self.jarvis.request_manager.cancel_active()
        if cancelled:
            print(f"[{cancelled.id}] REQUEST_CANCELLED by user")
        
        # Also stop any ongoing speech
        try:
            self.jarvis.stop_speaking()
        except Exception as e:
            print(f"Warning: Error stopping speech during cancellation: {e}")
        
        return cancelled

    def update_state(self, state, message):
        """Update UI based on Jarvis state changes."""
        # Update status light and label
        if state == "idle":
            self.status_light.setStyleSheet("""
                background-color: #00ff88;
                border-radius: 6px;
            """)
            self.status_label.setText("ONLINE")
            self.status_label.setStyleSheet("""
                color: #00ff88;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "listening":
            self.status_light.setStyleSheet("""
                background-color: #00ffff;
                border-radius: 6px;
            """)
            self.status_label.setText("LISTENING")
            self.status_label.setStyleSheet("""
                color: #00ffff;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "processing":
            self.status_light.setStyleSheet("""
                background-color: #ffaa00;
                border-radius: 6px;
            """)
            self.status_label.setText("PROCESSING")
            self.status_label.setStyleSheet("""
                color: #ffaa00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "searching":
            self.status_light.setStyleSheet("""
                background-color: #ff8800;
                border-radius: 6px;
            """)
            self.status_label.setText("SEARCHING")
            self.status_label.setStyleSheet("""
                color: #ff8800;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "response_ready":
            self.status_light.setStyleSheet("""
                background-color: #ffff00;
                border-radius: 6px;
            """)
            self.status_label.setText("RESPONSE READY")
            self.status_label.setStyleSheet("""
                color: #ffff00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "chat_updated":
            self.status_light.setStyleSheet("""
                background-color: #88ff00;
                border-radius: 6px;
            """)
            self.status_label.setText("RESPONSE DISPLAYED")
            self.status_label.setStyleSheet("""
                color: #88ff00;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "speaking":
            self.status_light.setStyleSheet("""
                background-color: #ff4488;
                border-radius: 6px;
            """)
            self.status_label.setText("SPEAKING")
            self.status_label.setStyleSheet("""
                color: #ff4488;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        elif state == "error":
            self.status_light.setStyleSheet("""
                background-color: #ff4444;
                border-radius: 6px;
            """)
            self.status_label.setText("ERROR")
            self.status_label.setStyleSheet("""
                color: #ff4444;
                font-family: 'Consolas', monospace;
                font-size: 11px;
                letter-spacing: 2px;
            """)
        
        # Update HUD state
        self.hud.set_state(state)
        
        # Disable Listen button during active operations to prevent duplicate requests
        busy_states = ["processing", "searching", "response_ready", "chat_updated", "speaking"]
        if state in busy_states:
            self.listen_button.setEnabled(False)
        else:
            self.listen_button.setEnabled(True)
        
        # Update status panel with contextual messages for live operations
        if "location" in message.lower() or "checking your location" in message.lower():
            display_msg = "Checking your location..."
        elif "weather" in message.lower() and ("getting" in message.lower() or "current" in message.lower()):
            display_msg = "Getting the latest weather..."
        elif "news" in message.lower() and ("latest" in message.lower() or "searching for current"):
            display_msg = "Searching for current news..."
        elif "timed out" in message.lower():
            display_msg = "The request timed out. Retrying..."
        else:
            display_msg = message
        
        self.status_panel.update_status(state, display_msg)

    def send_chat_message(self):
        """Send a chat message to Jarvis with proper response ordering."""
        text = self.chat_input.text().strip()
        if not text:
            return
        
        # Prevent duplicate submissions while processing
        if self.chat_processing or self.get_state() == "processing":
            return
        
        # Generate request ID via RequestManager
        request_id = self.next_request_id()
        
        # Clear input and disable controls during request
        self.chat_input.clear()
        self.chat_input.setEnabled(False)
        
        # Add user message to chat immediately
        self.add_chat_message("You", text, is_user=True)
        
        # Show "Thinking..." indicator in chat while processing
        thinking_msg = ChatMessageWidget("JARVIS", "Thinking...", is_user=False)
        thinking_msg.setObjectName(f"thinking_{request_id}")
        self.chat_layout.removeItem(self.chat_layout.itemAt(self.chat_layout.count() - 1))
        self.chat_layout.addWidget(thinking_msg)
        self.chat_layout.addStretch()
        
        # Show loading state and show Stop button
        self.set_state("processing", f"Processing: {text}")
        self.stop_chat_button.show()
        self.chat_processing = True
        
        def process_thread():
            try:
                if not self.jarvis:
                    QTimer.singleShot(0, lambda: self.add_chat_message("JARVIS", "Backend not initialized.", is_user=False))
                    QTimer.singleShot(0, lambda: self.set_state("idle", "Ready."))
                    return
                
                # Reset stop flags for new chat operation
                self.jarvis.reset_stop_flags()
                
                # Detect if this is a live/location query and show appropriate status
                text_lower = text.lower()
                if any(word in text_lower for word in ["weather", "temperature"]):
                    QTimer.singleShot(0, lambda: self.set_state("searching", "Checking your location..."))
                elif any(word in text_lower for word in ["news", "latest headlines", "breaking news"]):
                    QTimer.singleShot(0, lambda: self.set_state("searching", "Searching for current news..."))
                
                # Get response text without speaking first
                response_text, is_exit = self.jarvis.get_response_text(text)
                
                # Check if request was cancelled or superseded
                if not self.is_current_request(request_id):
                    print(f"[{request_id}] Request superseded or cancelled, discarding response")
                    # Remove thinking message if still present and reset UI state
                    def cleanup_superseded():
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        # Reset UI state so it's not stuck in processing
                        self.set_state("idle", "Ready for next command.")
                        self.chat_input.setEnabled(True)
                        self.stop_chat_button.hide()
                    QTimer.singleShot(0, cleanup_superseded)
                    return
                
                if response_text:
                    # Step 1: Mark response as ready
                    QTimer.singleShot(0, lambda: self.set_state("response_ready", "Response generated"))
                    
                    # Step 2: Replace "Thinking..." with actual response in chat BEFORE speaking
                    def replace_thinking_with_response(response):
                        """Replace the thinking message with the actual response."""
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    # Remove thinking message
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        
                        # Add actual response
                        self.add_chat_message("JARVIS", response, is_user=False)
                    
                    QTimer.singleShot(0, lambda r=response_text: replace_thinking_with_response(r))
                    
                    # Step 3: Mark chat as updated
                    QTimer.singleShot(0, lambda: self.set_state("chat_updated", "Response displayed"))
                    
                    # Step 4: Now speak the response (after it's visible in chat)
                    QTimer.singleShot(0, lambda: self.set_state("speaking", "Speaking response..."))
                    threading.Thread(target=self.jarvis.speak, args=(response_text,), daemon=True).start()
                
                if is_exit:
                    QApplication.instance().quit()
                
                # Step 5: Return to idle after speaking completes (or immediately for text-only)
                QTimer.singleShot(0, lambda: self.set_state("idle", "Ready for next command."))
            except ConnectionError as e:
                error_msg = str(e)
                print(f"[{request_id}] Connection error: {error_msg}")
                if self.is_current_request(request_id):
                    def show_connection_error(err):
                        # Remove thinking message first
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        self.add_chat_message("JARVIS", f"Connection Error: {err}", is_user=False)
                    QTimer.singleShot(0, lambda err=error_msg: show_connection_error(err))
                    QTimer.singleShot(0, lambda err=error_msg: self.set_state("error", err))
            except TimeoutError as e:
                error_msg = str(e)
                print(f"[{request_id}] Timeout error: {error_msg}")
                if self.is_current_request(request_id):
                    def show_timeout_error(err):
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        self.add_chat_message("JARVIS", f"Timeout: {err}", is_user=False)
                    QTimer.singleShot(0, lambda err=error_msg: show_timeout_error(err))
                    QTimer.singleShot(0, lambda err=error_msg: self.set_state("error", err))
            except ValueError as e:
                error_msg = str(e)
                print(f"[{request_id}] Value error: {error_msg}")
                if self.is_current_request(request_id):
                    def show_value_error(err):
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        self.add_chat_message("JARVIS", f"Error: {err}", is_user=False)
                    QTimer.singleShot(0, lambda err=error_msg: show_value_error(err))
                    QTimer.singleShot(0, lambda err=error_msg: self.set_state("error", err))
            except RuntimeError as e:
                error_msg = str(e)
                print(f"[{request_id}] Runtime error: {error_msg}")
                if self.is_current_request(request_id):
                    def show_runtime_error(err):
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        self.add_chat_message("JARVIS", f"Error: {err}", is_user=False)
                    QTimer.singleShot(0, lambda err=error_msg: show_runtime_error(err))
                    QTimer.singleShot(0, lambda err=error_msg: self.set_state("error", err))
            except Exception as e:
                import traceback
                error_msg = f"Error processing message: {e}"
                print(f"[{request_id}] {error_msg}")
                traceback.print_exc()
                if self.is_current_request(request_id):
                    def show_generic_error(err):
                        for i in range(self.chat_layout.count()):
                            item = self.chat_layout.itemAt(i)
                            if item and isinstance(item.widget(), ChatMessageWidget):
                                widget = item.widget()
                                if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                                    self.chat_layout.removeWidget(widget)
                                    widget.deleteLater()
                                    break
                        self.add_chat_message("JARVIS", f"Error: {err}", is_user=False)
                    QTimer.singleShot(0, lambda err=str(e): show_generic_error(err))
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", err))
            finally:
                # Re-enable controls and hide Stop button when done (only if still current)
                if self.is_current_request(request_id):
                    QTimer.singleShot(0, lambda: self.chat_input.setEnabled(True))
                    QTimer.singleShot(0, lambda: self.stop_chat_button.hide())
                    self.chat_processing = False
        
        thread = threading.Thread(target=process_thread, daemon=True)
        thread.start()

    def stop_chat(self):
        """Stop the current chat response (legacy name, now calls cancel)."""
        self.cancel_active_request()

    def cancel_active_request(self):
        """Cancel the currently active request and return to IDLE."""
        if not self.jarvis:
            return
        
        # Cancel via RequestManager
        cancelled = self.jarvis.request_manager.cancel_active()
        
        if cancelled:
            print(f"[{cancelled.id}] REQUEST_CANCELLED by user")
            
            # Stop any ongoing speech
            try:
                self.jarvis.stop_speaking()
            except Exception as e:
                print(f"Warning: Error stopping speech during cancellation: {e}")
        
        # Remove thinking message if present and show cancelled indicator
        def cleanup_thinking():
            for i in range(self.chat_layout.count()):
                item = self.chat_layout.itemAt(i)
                if item and isinstance(item.widget(), ChatMessageWidget):
                    widget = item.widget()
                    if hasattr(widget, 'objectName') and widget.objectName().startswith("thinking_"):
                        self.chat_layout.removeWidget(widget)
                        widget.deleteLater()
                        break
            self.add_chat_message("JARVIS", "Request cancelled.", is_user=False)
        
        # Hide the Stop button and re-enable controls
        QTimer.singleShot(0, cleanup_thinking)
        QTimer.singleShot(0, lambda: self.stop_chat_button.hide())
        QTimer.singleShot(0, lambda: self.chat_input.setEnabled(True))
        self.chat_processing = False
        
        # Reset state to idle with clear message
        QTimer.singleShot(0, lambda: self.set_state("idle", "Request cancelled."))

    def _auto_stop_listening(self):
        """Automatically stop listening after timeout."""
        print("Auto-stopping listening (5 second timeout)")
        # Just signal the backend to stop - let the listen thread handle state transitions
        if self.jarvis:
            try:
                self.jarvis.stop_listening()
            except Exception as e:
                print(f"Warning: Could not signal stop listening on auto-stop: {e}")

    def toggle_listening(self):
        """Toggle listening state with atomic transitions."""
        with self.state_lock:
            if self.is_listening:
                # Stop listening - signal the backend to stop and process captured audio
                print("User requested stop listening")
                self.is_listening = False
                # Set button text directly (we're on main thread from button click)
                self.listen_button.setText("LISTEN")
                if hasattr(self, 'listen_timer') and self.listen_timer.isActive():
                    self.listen_timer.stop()
                if self.jarvis:
                    try:
                        self.jarvis.stop_listening()
                    except Exception as e:
                        print(f"Warning: Could not signal stop listening: {e}")
            else:
                # Start listening - only from idle state (atomic check-and-set)
                current = self.current_state
                if current != "idle":
                    print(f"Duplicate listening request ignored (state={current})")
                    # Show feedback to user that Jarvis is busy - use set_state for synchronized UI update
                    busy_messages = {
                        "processing": "Processing your request...",
                        "searching": "Searching the web...",
                        "response_ready": "Preparing response...",
                        "chat_updated": "Displaying response...",
                        "speaking": "Speaking..."
                    }
                    msg = busy_messages.get(current, f"Busy ({current})")
                    self.set_state(current, msg)
                    return
                
                self.is_listening = True
                # Set button text directly (we're on main thread from button click)
                self.listen_button.setText("STOP LISTENING")
        
        # Start the actual listening thread outside the lock
        if self.is_listening:
            self.start_listening()

    def start_listening(self):
        """Start listening for voice input."""
        if not self.jarvis:
            self.set_state("error", "Jarvis backend not initialized.")
            return
        
        print("STATE: IDLE -> LISTENING")
        # Button text already set in toggle_listening; no need to set again here
        self.set_state("listening", "Listening for your command...")
        
        # Auto-stop timer: stop listening after 5 seconds if user hasn't manually stopped
        self.listen_timer = QTimer()
        self.listen_timer.setSingleShot(True)
        self.listen_timer.timeout.connect(self._auto_stop_listening)
        self.listen_timer.start(5000)  # 5 second timeout
        
        def listen_thread():
            command_processed = False  # Track if we transitioned to processing a command
            try:
                # Single listening session - capture audio then transcribe
                try:
                    print("Listening session started")
                    audio_data = self.jarvis.listen()
                    print("Listening session stopped by user or timeout")
                except TimeoutError as e:
                    # No speech detected - show error and return to idle
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", f"No speech detected"))
                    QTimer.singleShot(3000, lambda: self.set_state("idle", "Ready for next command."))
                    with self.state_lock:
                        self.is_listening = False
                    return
                except PermissionError as e:
                    # Microphone permission error - stop listening
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", f"Microphone permission denied"))
                    with self.state_lock:
                        self.is_listening = False
                    return
                except RuntimeError as e:
                    # Other runtime errors (service down, etc.)
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", str(e)))
                    with self.state_lock:
                        self.is_listening = False
                    return
                
                if not audio_data:
                    print("STATE: LISTENING -> IDLE")
                    QTimer.singleShot(0, lambda: self.set_state("idle", "Ready for next command."))
                    with self.state_lock:
                        self.is_listening = False
                    return
                
                # Post-capture transcription - convert audio to text after listening stops
                try:
                    print("Transcribing captured audio...")
                    command = self.jarvis.recognize_audio(audio_data)
                except ValueError as e:
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", f"Could not understand speech"))
                    QTimer.singleShot(3000, lambda: self.set_state("idle", "Ready for next command."))
                    with self.state_lock:
                        self.is_listening = False
                    return
                except RuntimeError as e:
                    QTimer.singleShot(0, lambda err=str(e): self.set_state("error", str(e)))
                    with self.state_lock:
                        self.is_listening = False
                    return
                
                if not command or len(command.strip()) == 0:
                    print("STATE: LISTENING -> IDLE")
                    QTimer.singleShot(0, lambda: self.set_state("idle", "Ready for next command."))
                    with self.state_lock:
                        self.is_listening = False
                    return
                
                # Display transcribed text in chat so user can verify what was heard
                self.add_chat_message("You", command, is_user=True)
                
                # Check for stop phrases
                command_lower = command.lower()
                if any(phrase in command_lower for phrase in ["bye", "goodbye", "stop listening"]):
                    print(f"STATE: LISTENING -> PROCESSING (exit command)")
                    QTimer.singleShot(0, lambda c=command: self.set_state("processing", f"Processing: {c}"))
                    
                    # Get response text without speaking first
                    try:
                        response_text, is_exit = self.jarvis.get_response_text(command)
                        if response_text:
                            # Display in chat before speaking
                            QTimer.singleShot(0, lambda r=response_text: self.add_chat_message("JARVIS", r, is_user=False))
                            QTimer.singleShot(0, lambda: self.set_state("chat_updated", "Response displayed"))
                            # Speak after adding to chat
                            threading.Thread(target=self.jarvis.speak, args=(response_text,), daemon=True).start()
                        if is_exit:
                            QApplication.instance().quit()
                    except Exception as e:
                        print(f"Error processing exit command: {e}")
                    
                    QTimer.singleShot(0, lambda: self.listen_button.setText("LISTEN"))
                    print("STATE: PROCESSING -> IDLE")
                    QTimer.singleShot(0, lambda: self.set_state("idle", "Stopped listening."))
                    with self.state_lock:
                        self.is_listening = False
                    return
                
                # Process command normally - add to chat and process
                print(f"STATE: LISTENING -> PROCESSING")
                QTimer.singleShot(0, lambda c=command: self.set_state("processing", f"Processing: {c}"))
                
                # Mark as no longer listening before spawning process thread
                with self.state_lock:
                    self.is_listening = False
                
                # Process in a separate thread so UI stays responsive
                def process_voice_command(cmd):
                    try:
                        # Get response text without speaking first
                        response_text, is_exit = self.jarvis.get_response_text(cmd)
                        
                        if response_text:
                            # Display in chat before speaking
                            QTimer.singleShot(0, lambda r=response_text: self.add_chat_message("JARVIS", r, is_user=False))
                            QTimer.singleShot(0, lambda: self.set_state("chat_updated", "Response displayed"))
                            # Speak after adding to chat (async)
                            threading.Thread(target=self.jarvis.speak, args=(response_text,), daemon=True).start()
                        
                        if is_exit:
                            QApplication.instance().quit()
                    except Exception as e:
                        print(f"Error processing voice command: {e}")
                        QTimer.singleShot(0, lambda err=str(e): self.set_state("error", f"Error: {err}"))
                    finally:
                        # Always return to idle after processing completes
                        QTimer.singleShot(0, lambda: self.listen_button.setText("LISTEN"))
                        print("STATE: PROCESSING -> IDLE")
                        QTimer.singleShot(0, lambda: self.set_state("idle", "Ready for next command."))
                
                proc_thread = threading.Thread(target=process_voice_command, args=(command,), daemon=True)
                proc_thread.start()
                
            except Exception as e:
                import traceback
                error_msg = f"Error in listen thread: {e}"
                print(error_msg)
                traceback.print_exc()
            
            finally:
                # Always return to idle state after listening session ends
                with self.state_lock:
                    self.is_listening = False
                
                # Stop the auto-stop timer safely from main thread to prevent
                # QObject::killTimer warnings about cross-thread timer access
                if hasattr(self, 'listen_timer'):
                    QTimer.singleShot(0, lambda t=self.listen_timer: (t.stop() if t.isActive() else None))
                
                QTimer.singleShot(0, lambda: self.listen_button.setText("LISTEN"))
                if self.get_state() == "listening":
                    print("STATE: LISTENING -> IDLE")
                    QTimer.singleShot(0, lambda: self.set_state("idle", "Ready for next command."))
        
        thread = threading.Thread(target=listen_thread, daemon=True)
        thread.start()


def main():
    """Main entry point for the Jarvis frontend."""
    app = QApplication(sys.argv)
    
    # Set application-wide font
    font = QFont('Segoe UI', 10)
    app.setFont(font)
    
    window = JarvisFrontend()
    window.show()
    
    # Clean up generated test-output files on normal shutdown
    def cleanup_on_exit():
        try:
            from tests.test_output_manager import cleanup_test_output
            deleted = cleanup_test_output()
            if deleted:
                print(f"Cleaned up {len(deleted)} test output file(s) on exit")
        except Exception as e:
            # Continue shutdown even if cleanup fails
            print(f"Warning: Test output cleanup failed during shutdown: {e}")
    
    app.aboutToQuit.connect(cleanup_on_exit)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()