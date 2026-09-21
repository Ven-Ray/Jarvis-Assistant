"""
Audio Waveform Visualizer - Animated waveform display for audio input.
Shows real-time amplitude visualization with futuristic styling.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QPainter, QPen, QColor, QPolygonF
import math


class WaveformVisualizer(QWidget):
    """Animated audio waveform visualizer."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.setMinimumHeight(80)
        
        # Animation state
        self.is_active = False
        self.wave_phase = 0
        
        # Generate random amplitude data for idle animation
        import random
        self.amplitudes = [random.uniform(0.1, 0.3) for _ in range(50)]
        
        # Animation timer
        self.animation_timer = QTimer(self)
        self.animation_timer.timeout.connect(self.animate)
        self.animation_timer.start(33)  # ~30 FPS
    
    def set_active(self, active):
        """Set whether the visualizer is actively receiving audio."""
        self.is_active = active
    
    def update_amplitudes(self, amplitudes):
        """Update waveform with new amplitude data."""
        if len(amplitudes) == 50:
            self.amplitudes = amplitudes
    
    def animate(self):
        """Animate the waveform even when idle."""
        import random
        
        if not self.is_active:
            # Generate subtle idle animation
            for i in range(len(self.amplitudes)):
                base = 0.15 + 0.05 * (i / len(self.amplitudes))
                noise = random.uniform(-0.03, 0.03)
                self.amplitudes[i] = max(0.05, min(0.4, base + noise))
        
        self.wave_phase += 2
        self.update()
    
    def paintEvent(self, event):
        """Draw the waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        width = self.width()
        height = self.height()
        
        # Background grid lines (subtle)
        painter.setPen(QPen(QColor(0, 255, 255, 30), 1))
        for y in range(0, height, 20):
            painter.drawLine(0, y, width, y)
        
        # Draw waveform as connected line segments
        color = QColor(0, 255, 255) if self.is_active else QColor(0, 255, 255, 150)
        pen = QPen(color, 2)
        painter.setPen(pen)
        
        # Calculate points for the waveform
        num_points = len(self.amplitudes)
        segment_width = width / (num_points - 1)
        
        path = []
        for i, amp in enumerate(self.amplitudes):
            x = i * segment_width
            y_offset = amp * (height // 2)
            
            # Top point
            top_y = height // 2 - int(y_offset)
            # Bottom point  
            bottom_y = height // 2 + int(y_offset)
            
            path.append((int(x), top_y))
        
        # Draw the waveform line using polyline
        if len(path) > 1:
            points = [QPoint(p[0], p[1]) for p in path]
            painter.drawPolyline(points)
            
            # Mirror below center
            mirror_points = []
            for i in range(len(path) - 1, -1, -1):
                mirror_points.append(QPoint(path[i][0], height - path[i][1] + 1))
            painter.drawPolyline(mirror_points)
        
        # Draw center line
        painter.setPen(QPen(QColor(0, 255, 255, 80), 1))
        painter.drawLine(0, height // 2, width, height // 2)
        
        painter.end()