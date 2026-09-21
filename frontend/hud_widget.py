"""
Circular HUD Widget - Futuristic animated circular interface.
Features rotating rings, pulsing core, and state-based animations.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QRadialGradient


class CircularHUD(QWidget):
    """Futuristic circular HUD with animated rings and pulsing core."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumSize(300, 300)
        self.setFixedHeight(400)
        
        # Animation state
        self.current_state = "idle"
        self.rotation_angle = 0
        self.pulse_phase = 0
        self.inner_rotation = 0
        
        # Colors for different states
        self.state_colors = {
            "idle": QColor(0, 255, 136),      # Green
            "listening": QColor(0, 255, 255), # Cyan
            "processing": QColor(255, 170, 0),# Orange
            "speaking": QColor(255, 68, 136), # Pink
            "error": QColor(255, 68, 68)      # Red
        }
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(16)  # ~60 FPS
    
    def set_state(self, state):
        """Update the HUD state and color."""
        self.current_state = state
    
    def animate(self):
        """Update animation parameters each frame."""
        # Rotate outer ring slowly
        self.rotation_angle = (self.rotation_angle + 0.5) % 360
        
        # Inner ring rotates faster in opposite direction
        self.inner_rotation = (self.inner_rotation - 1.0) % 360
        
        # Pulse effect based on state
        if self.current_state == "listening":
            self.pulse_phase = (self.pulse_phase + 5) % 360
        elif self.current_state == "processing":
            self.pulse_phase = (self.pulse_phase + 10) % 360
        
        self.update()
    
    def paintEvent(self, event):
        """Draw the circular HUD."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        center_x = width // 2
        center_y = height // 2
        
        # Determine radius based on smaller dimension
        radius = min(width, height) // 2 - 20
        
        # Get current state color
        base_color = self.state_colors.get(self.current_state, QColor(0, 255, 136))
        
        # Draw outer decorative ring (static)
        painter.setPen(QPen(base_color.darker(150), 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center_x - radius, center_y - radius, 
                           radius * 2, radius * 2)
        
        # Draw rotating outer ring with tick marks
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        
        # Tick marks around the circle
        for i in range(60):
            angle = i * 6
            is_major = (i % 10 == 0)
            
            if is_major:
                pen = QPen(base_color, 2)
                inner_r = radius - 15
            else:
                pen = QPen(base_color.lighter(130), 1)
                inner_r = radius - 8
            
            painter.setPen(pen)
            
            import math
            rad = math.radians(angle)
            x1 = inner_r * math.cos(rad)
            y1 = inner_r * math.sin(rad)
            x2 = (radius - 3) * math.cos(rad)
            y2 = (radius - 3) * math.sin(rad)
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.restore()
        
        # Draw inner rotating ring with segments
        painter.save()
        painter.translate(center_x, center_y)
        painter.rotate(self.inner_rotation)
        
        inner_radius = radius - 30
        
        # Draw segmented arc (like a loading indicator)
        for i in range(8):
            start_angle = i * 45
            span_angle = 30
            
            pen = QPen(base_color, 3)
            painter.setPen(pen)
            
            import math
            start_rad = math.radians(start_angle)
            end_rad = math.radians(start_angle + span_angle)
            
            # Draw arc segment
            x1 = inner_radius * math.cos(start_rad)
            y1 = inner_radius * math.sin(start_rad)
            x2 = inner_radius * math.cos(end_rad)
            y2 = inner_radius * math.sin(end_rad)
            
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))
        
        painter.restore()
        
        # Draw pulsing core circle
        import math
        
        if self.current_state == "listening" or self.current_state == "processing":
            pulse = 0.8 + 0.2 * math.sin(math.radians(self.pulse_phase))
        else:
            pulse = 1.0
        
        core_radius = int((radius - 60) * pulse)
        
        # Core glow effect
        painter.setPen(Qt.PenStyle.NoPen)
        gradient = QRadialGradient(center_x, center_y, core_radius + 20)
        gradient.setColorAt(0.0, base_color.lighter(150))
        gradient.setColorAt(0.7, base_color)
        gradient.setColorAt(1.0, QColor(base_color.red(), base_color.green(), 
                                       base_color.blue(), 0))
        painter.setBrush(QBrush(gradient))
        painter.drawEllipse(center_x - core_radius - 20, center_y - core_radius - 20,
                           (core_radius + 20) * 2, (core_radius + 20) * 2)
        
        # Solid core
        painter.setBrush(QBrush(base_color.darker(150)))
        painter.drawEllipse(center_x - core_radius, center_y - core_radius,
                           core_radius * 2, core_radius * 2)
        
        # State text in center
        state_text = self.current_state.upper()
        font = QFont('Consolas', 14, QFont.Weight.Bold)
        painter.setFont(font)
        painter.setPen(QPen(base_color.lighter(150)))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, state_text)
        
        # Decorative dots around the circle
        for i in range(12):
            angle = i * 30 + self.rotation_angle / 2
            import math
            rad = math.radians(angle)
            dot_x = center_x + (radius - 5) * math.cos(rad)
            dot_y = center_y + (radius - 5) * math.sin(rad)
            
            painter.setPen(Qt.PenStyle.NoPen)
            if i % 3 == 0:
                painter.setBrush(QBrush(base_color))
            else:
                painter.setBrush(QBrush(base_color.lighter(120)))
            painter.drawEllipse(int(dot_x - 2), int(dot_y - 2), 4, 4)
        
        painter.end()