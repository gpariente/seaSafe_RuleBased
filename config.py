# config.py
"""
Central Configuration Module

This module defines global constants and layout parameters used throughout the SeaSafe Simulator.
It includes base resolutions for various application states, layout margins, color definitions,
default font size, and background scrolling speed.
"""

# Base resolutions for different application states (width, height)
BASE_RESOLUTIONS = {
    "main_menu": (800, 600),
    "auto_mode": (800, 600),
    "manual_scenario": (800, 600),
    "manual_ship_setup": (900, 700),
    "simulation": (880, 920),
    "stats": (800, 840)
}

# Margins and layout parameters for the simulation screen
LEFT_MARGIN = 60       # Left margin in pixels
TOP_MARGIN = 20        # Top margin in pixels
RIGHT_MARGIN = 20      # Right margin in pixels
BOTTOM_MARGIN = 60     # Bottom margin in pixels
UI_PANEL_HEIGHT = 40   # Height of the UI panel at the bottom

# Color definitions (RGB tuples)
BG_COLOR = (130, 180, 255)       # Background color (blueish)
OVERLAY_COLOR = (0, 0, 0, 100)   # Overlay color with transparency (black with 100 alpha)
UI_PANEL_COLOR = (60, 60, 60)     # UI panel color (dark grey)

# Default font size used throughout the application
DEFAULT_FONT_SIZE = 28

# Background scrolling speed (pixels per second at base resolution)
BG_SCROLL_SPEED = 30
