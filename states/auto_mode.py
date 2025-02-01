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

class AutoModeState:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.next_state = None
        self.base_resolution = BASE_RESOLUTIONS["auto_mode"]
        self.buttons = {
            "back": pygame.Rect(50, 500, 100, 40),
            "load": pygame.Rect(300, 250, 200, 50),  # Moved down to avoid logo
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
                        self.json_data = data
                        self.automatic_loaded_ok = True
                        self.warning_msg = "JSON loaded successfully."
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
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font,color=(0,100,180))
        draw_button(screen, self.scaled_buttons["load"], "Load JSON", self.font,color=(0,100,180))
        draw_button(screen, self.scaled_buttons["start"], "Start", self.font,color=(0,100,180))
        if self.warning_msg:
            warning = self.font.render(self.warning_msg, True, (255,0,0))
            screen.blit(warning, (int(200 * self.scale_x), int(450 * self.scale_y)))
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
