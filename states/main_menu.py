# states/main_menu.py
import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from draw_utils import draw_button, draw_scrolling_bg
from states.manual_scenario import ManualScenarioState
from states.auto_mode import AutoModeState

class MainMenuState:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.next_state = None
        self.base_resolution = BASE_RESOLUTIONS["main_menu"]
        # Define base button positions (x, y, width, height)
        self.buttons = {
            "manual": pygame.Rect((self.base_resolution[0] - 200) // 2, 250, 200, 50),
            "auto": pygame.Rect((self.base_resolution[0] - 200) // 2, 340, 200, 50),
            "exit": pygame.Rect((self.base_resolution[0] - 200) // 2, 430, 200, 50)
        }
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.bg_img = None
        self.logo_img = None
        self.bg_scroll_x = 0.0  # For background scrolling

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                if self.scaled_buttons["manual"].collidepoint(pos):
                    self.next_state = ManualScenarioState(self.screen)
                elif self.scaled_buttons["auto"].collidepoint(pos):
                    self.next_state = AutoModeState(self.screen)
                elif self.scaled_buttons["exit"].collidepoint(pos):
                    pygame.quit()
                    exit()
    
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
        # Load background if not loaded
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None
        # Update background scroll position if background exists
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(self.screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, dt)
    
    def render(self, screen):
        # If background image exists, it was already drawn by update (draw_scrolling_bg)
        if not self.bg_img:
            screen.fill(BG_COLOR)
        # Draw logo if available
        if self.logo_img is None:
            try:
                self.logo_img = pygame.image.load("./images/logo.png").convert_alpha()
                # Scale logo by factor of 2 (base size)
                self.logo_img = pygame.transform.scale(self.logo_img, (self.logo_img.get_width() * 2,
                                                                       self.logo_img.get_height() * 2))
            except:
                self.logo_img = None
        if self.logo_img:
            logo_x = (screen.get_width() - self.logo_img.get_width()) // 2
            logo_y = int(30 * self.scale_y)
            screen.blit(self.logo_img, (logo_x, logo_y))
        # Draw buttons
        draw_button(screen, self.scaled_buttons["manual"], "Manual Mode", self.font, color=(0,100,180))
        draw_button(screen, self.scaled_buttons["auto"], "Automatic Mode", self.font, color=(0,100,180))
        draw_button(screen, self.scaled_buttons["exit"], "Exit", self.font, color=(0,100,180))
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
