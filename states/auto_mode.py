# states/auto_mode.py
"""
Auto Mode State Module

This module provides the AutoModeState class used for the automatic setup mode in SeaSafe.
In this mode, the user can load a JSON file containing a scenario setup. The JSON data is
validated against a set of rules (e.g., map size, safety zone, heading range, and per-ship data).
If the JSON data is valid, the simulation will start using the loaded scenario.

It also provides helper functions:
    - load_json_file(): Opens a file dialog for the user to select a JSON file and loads it.
    - validate_json_data(data): Validates the JSON data against required rules.

"""

import pygame
import json
import tkinter as tk
import tkinter.filedialog as fd
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from draw_utils import draw_button, draw_scrolling_bg
from states.simulation_ui import SimulationState

def load_json_file():
    """
    Opens a file dialog to allow the user to select a JSON file and loads the file.

    Returns:
        dict or None: The JSON data as a dictionary if loaded successfully; otherwise, None.
    """
    root = tk.Tk()
    root.withdraw()  # Hide the main Tkinter window.
    file_path = fd.askopenfilename(filetypes=[("JSON Files", "*.json")])
    root.destroy()
    if file_path:
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return data
        except Exception as e:
            return None
    return None

def validate_json_data(data):
    """
    Validates the JSON data against a set of rules:
      - "map_size": Must be positive and ≤ 20.
      - "safe_distance": Must be positive.
      - "heading_range": Must be positive and ≤ 90.
      - "heading_step": Must be positive.
      - "time_step": Must be positive.
      - "ships": Must be a list with 2 to 8 elements.
      For each ship dictionary, the following must be true:
          - "start_x", "start_y", "dest_x", "dest_y": Must be numbers between 0 and map_size.
          - "speed": Must be > 0 and ≤ 50.
          - "length_m": Must be > 0 and ≤ 800.
          - "width_m": Must be > 0 and ≤ 200.

    Parameters:
        data (dict): The JSON data loaded from file.

    Returns:
        tuple: (is_valid (bool), message (str))
               If valid, returns (True, "JSON loaded successfully.").
               Otherwise, returns (False, "<appropriate error message>").
    """
    try:
        map_size = float(data.get("map_size", 0))
        if map_size <= 0 or map_size > 20:
            return (False, "Map Size must be > 0 and ≤ 20.")
        safe_distance = float(data.get("safe_distance", 0))
        if safe_distance <= 0:
            return (False, "Safety Zone must be positive.")
        heading_range = float(data.get("heading_range", 0))
        if heading_range <= 0 or heading_range > 90:
            return (False, "Heading Range must be > 0 and ≤ 90.")
        heading_step = float(data.get("heading_step", 0))
        if heading_step <= 0:
            return (False, "Heading Step must be positive.")
        time_step = float(data.get("time_step", 0))
        if time_step <= 0:
            return (False, "Time Step must be positive.")

        ships = data.get("ships", [])
        num_ships = len(ships)
        if num_ships < 2 or num_ships > 8:
            return (False, "#Ships must be between 2 and 8.")

        for i, ship in enumerate(ships):
            # Validate start coordinates.
            sx = float(ship.get("start_x", -1))
            sy = float(ship.get("start_y", -1))
            if sx < 0 or sy < 0 or sx > map_size or sy > map_size:
                return (False, f"Ship {i+1} start coordinates must be between 0 and {map_size}.")
            # Validate destination coordinates.
            dx = float(ship.get("dest_x", -1))
            dy = float(ship.get("dest_y", -1))
            if dx < 0 or dy < 0 or dx > map_size or dy > map_size:
                return (False, f"Ship {i+1} destination coordinates must be between 0 and {map_size}.")
            # Validate speed.
            speed = float(ship.get("speed", 0))
            if speed <= 0 or speed > 50:
                return (False, f"Ship {i+1} speed must be > 0 and ≤ 50.")
            # Validate length and width.
            length_m = float(ship.get("length_m", 0))
            if length_m <= 0 or length_m > 800:
                return (False, f"Ship {i+1} length must be > 0 and ≤ 800.")
            width_m = float(ship.get("width_m", 0))
            if width_m <= 0 or width_m > 200:
                return (False, f"Ship {i+1} width must be > 0 and ≤ 200.")
    except Exception as e:
        return (False, "Invalid numeric value in JSON data.")
    return (True, "JSON loaded successfully.")

class AutoModeState:
    def __init__(self, screen):
        """
        Initializes the AutoModeState.

        Parameters:
            screen (pygame.Surface): The main display surface.
        """
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.next_state = None
        self.base_resolution = BASE_RESOLUTIONS["auto_mode"]
        # Define buttons for navigation.
        self.buttons = {
            "back": pygame.Rect(50, 500, 100, 40),
            "load": pygame.Rect(300, 250, 200, 50),  # Positioned to avoid overlap with the logo.
            "start": pygame.Rect(300, 350, 200, 50)
        }
        self.warning_msg = ""           # Holds warning or status messages.
        self.automatic_loaded_ok = False  # Flag indicating whether valid JSON data has been loaded.
        self.json_data = None           # Holds the loaded JSON data.
        self.bg_img = None              # Background image.
        self.logo_img = None            # Logo image.
        self.bg_scroll_x = 0.0          # Current horizontal scroll offset for the background.

    def handle_events(self, events):
        """
        Handles Pygame events for the auto mode state.

        Parameters:
            events (list): List of Pygame events.
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.scaled_buttons["back"].collidepoint(pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
                elif self.scaled_buttons["load"].collidepoint(pos):
                    data = load_json_file()
                    if data is not None:
                        valid, msg = validate_json_data(data)
                        if valid:
                            self.json_data = data
                            self.automatic_loaded_ok = True
                            self.warning_msg = msg
                        else:
                            self.warning_msg = msg
                            self.automatic_loaded_ok = False
                    else:
                        self.warning_msg = "Error: Could not load JSON file!"
                        self.automatic_loaded_ok = False
                elif self.scaled_buttons["start"].collidepoint(pos):
                    if self.automatic_loaded_ok:
                        scenario_data = self.json_data
                        self.next_state = SimulationState(self.screen, scenario_data)
                    else:
                        self.warning_msg = "No valid JSON loaded!"
    
    def update(self, dt):
        """
        Updates the state of the AutoMode screen, including scaling UI elements and background.

        Parameters:
            dt (float): The elapsed time in seconds since the last update.
        """
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        self.scale_x = current_w / base_w
        self.scale_y = current_h / base_h
        self.scaled_buttons = {}
        for key, rect in self.buttons.items():
            self.scaled_buttons[key] = pygame.Rect(
                int(rect.x * self.scale_x),
                int(rect.y * self.scale_y),
                int(rect.width * self.scale_x),
                int(rect.height * self.scale_y)
            )
        # Load and update background image.
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(self.screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, dt)
        # Load logo if not already loaded.
        if self.logo_img is None:
            try:
                self.logo_img = pygame.image.load("./images/logo.png").convert_alpha()
                self.logo_img = pygame.transform.scale(self.logo_img, (self.logo_img.get_width() * 2,
                                                                       self.logo_img.get_height() * 2))
            except:
                self.logo_img = None

    def render(self, screen):
        """
        Renders the AutoMode state UI, including background, logo, buttons, and warning messages.

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        # Draw background (if already drawn in update, no further action needed).
        if self.bg_img:
            pass
        else:
            screen.fill(BG_COLOR)
        # Draw logo at the top center.
        if self.logo_img:
            logo_x = (screen.get_width() - self.logo_img.get_width()) // 2
            logo_y = int(30 * self.scale_y)
            screen.blit(self.logo_img, (logo_x, logo_y))
        # Draw UI buttons.
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font, color=(0, 100, 180))
        draw_button(screen, self.scaled_buttons["load"], "Load JSON", self.font, color=(0, 100, 180))
        draw_button(screen, self.scaled_buttons["start"], "Start", self.font, color=(0, 100, 180))
        # Display any warning or status message.
        if self.warning_msg:
            warning = self.font.render(self.warning_msg, True, (255, 0, 0))
            screen.blit(warning, (int(200 * self.scale_x), int(450 * self.scale_y)))
    
    def get_next_state(self):
        """
        Retrieves the next state to transition to, if any.

        Returns:
            The next state object or None if no transition is requested.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
