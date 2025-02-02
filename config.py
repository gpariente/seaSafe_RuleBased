# config.py
# Central configuration for constants and layout parameters

BASE_RESOLUTIONS = {
    "main_menu": (800, 600),
    "auto_mode": (800, 600),
    "manual_scenario": (800, 600),
    "manual_ship_setup": (900, 700),
    "simulation": (880, 920),  
    "stats": (800, 840)
}

# Margins and layout for the simulation screen
LEFT_MARGIN = 60
TOP_MARGIN = 20
RIGHT_MARGIN = 20
BOTTOM_MARGIN = 60
UI_PANEL_HEIGHT = 40

# Colors
BG_COLOR = (130, 180, 255)
OVERLAY_COLOR = (0, 0, 0, 100)
UI_PANEL_COLOR = (60, 60, 60)

# Default font size
DEFAULT_FONT_SIZE = 28

# Background scrolling speed (pixels per second at base resolution)
BG_SCROLL_SPEED = 30
