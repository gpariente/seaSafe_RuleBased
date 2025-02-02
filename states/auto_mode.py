# states/auto_mode.py
import pygame
import json
import tkinter as tk
import tkinter.filedialog as fd
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from draw_utils import draw_button, draw_scrolling_bg
from states.simulation_ui import SimulationState

def load_json_file():
    root = tk.Tk()
    root.withdraw()
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
    Validate the JSON data according to the following rules:
      - "map_size": positive, ≤ 20
      - "safe_distance": positive
      - "heading_range": positive, ≤ 90
      - "heading_step": positive
      - "time_step": positive
      - "ships": list of ships with count between 2 and 8
      For each ship (assumed to be a dict):
          - "start_x", "start_y", "dest_x", "dest_y": numbers between 0 and map_size
          - "speed": > 0 and ≤ 50
          - "length_m": > 0 and ≤ 800
          - "width_m": > 0 and ≤ 200
    Returns a tuple (is_valid, message).
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
            # Validate start coordinates
            sx = float(ship.get("start_x", -1))
            sy = float(ship.get("start_y", -1))
            if sx < 0 or sy < 0 or sx > map_size or sy > map_size:
                return (False, f"Ship {i+1} start coordinates must be between 0 and {map_size}.")
            # Validate destination coordinates
            dx = float(ship.get("dest_x", -1))
            dy = float(ship.get("dest_y", -1))
            if dx < 0 or dy < 0 or dx > map_size or dy > map_size:
                return (False, f"Ship {i+1} destination coordinates must be between 0 and {map_size}.")
            # Validate speed
            speed = float(ship.get("speed", 0))
            if speed <= 0 or speed > 50:
                return (False, f"Ship {i+1} speed must be > 0 and ≤ 50.")
            # Validate length and width
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
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.next_state = None
        self.base_resolution = BASE_RESOLUTIONS["auto_mode"]
        self.buttons = {
            "back": pygame.Rect(50, 500, 100, 40),
            "load": pygame.Rect(300, 250, 200, 50),  
            "start": pygame.Rect(300, 350, 200, 50)
        }
        self.warning_msg = ""
        self.automatic_loaded_ok = False
        self.json_data = None
        self.bg_img = None
        self.logo_img = None
        self.bg_scroll_x = 0.0

    def handle_events(self, events):
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
        # Load and update background image
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(self.screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, dt)
        # Load logo (if not loaded)
        if self.logo_img is None:
            try:
                self.logo_img = pygame.image.load("./images/logo.png").convert_alpha()
                self.logo_img = pygame.transform.scale(self.logo_img, (self.logo_img.get_width() * 2,
                                                                       self.logo_img.get_height() * 2))
            except:
                self.logo_img = None

    def render(self, screen):
        # Draw background
        if self.bg_img:
            # Background already drawn in update via draw_scrolling_bg
            pass
        else:
            screen.fill(BG_COLOR)
        # Draw logo at top (so buttons appear below)
        if self.logo_img:
            logo_x = (screen.get_width() - self.logo_img.get_width()) // 2
            logo_y = int(30 * self.scale_y)
            screen.blit(self.logo_img, (logo_x, logo_y))
        # Draw buttons
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font, color=(0,100,180))
        draw_button(screen, self.scaled_buttons["load"], "Load JSON", self.font, color=(0,100,180))
        draw_button(screen, self.scaled_buttons["start"], "Start", self.font, color=(0,100,180))
        if self.warning_msg:
            warning = self.font.render(self.warning_msg, True, (255,0,0))
            screen.blit(warning, (int(200 * self.scale_x), int(450 * self.scale_y)))
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
