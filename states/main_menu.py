# states/main_menu.py
"""
Main Menu State Module

This module defines the MainMenuState class, which implements the main menu screen for the SeaSafe Simulator.
It displays the main menu UI (background, logo, and buttons) and handles user interactions to transition
to the Manual Mode, Automatic Mode, or exit the application.

"""

import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from draw_utils import draw_button, draw_scrolling_bg
from resource_path import resource_path
from states.manual_scenario import ManualScenarioState
from states.auto_mode import AutoModeState

class MainMenuState:
    def __init__(self, screen):
        """
        Initializes the Main Menu state.

        Parameters:
            screen (pygame.Surface): The main display surface.
        """
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
        self.bg_img = None      # Background image
        self.logo_img = None    # Logo image
        self.bg_scroll_x = 0.0  # Horizontal scroll offset for the background

    def handle_events(self, events):
        """
        Processes the list of Pygame events for the main menu.

        Parameters:
            events (list): List of Pygame events.
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = event.pos
                # Check if the Manual Mode button was clicked.
                if self.scaled_buttons["manual"].collidepoint(pos):
                    self.next_state = ManualScenarioState(self.screen)
                # Check if the Automatic Mode button was clicked.
                elif self.scaled_buttons["auto"].collidepoint(pos):
                    self.next_state = AutoModeState(self.screen)
                # Check if the Exit button was clicked.
                elif self.scaled_buttons["exit"].collidepoint(pos):
                    pygame.quit()
                    exit()

    def update(self, dt):
        """
        Updates the main menu state.

        This function scales the button positions according to the current screen size and
        updates the background scrolling offset.

        Parameters:
            dt (float): Elapsed time in seconds since the last update.
        """
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        # Calculate scale factors for horizontal and vertical dimensions.
        self.scale_x = current_w / base_w
        self.scale_y = current_h / base_h
        self.scaled_buttons = {}
        # Scale each button's rectangle.
        for key, rect in self.buttons.items():
            self.scaled_buttons[key] = pygame.Rect(
                int(rect.x * self.scale_x),
                int(rect.y * self.scale_y),
                int(rect.width * self.scale_x),
                int(rect.height * self.scale_y)
            )
        # Load background image if not already loaded.
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load(resource_path("images/sea_bg.png")).convert()
            except Exception as e:
                print("Error loading sea_bg:", e)
                self.bg_img = pygame.Surface((800, 600))
                self.bg_img.fill((0, 100, 200))

        # Update background scroll position if a background image is available.
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(self.screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, dt)

    def render(self, screen):
        """
        Renders the main menu screen, including background, logo, and buttons.

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        # If the background image exists, it was drawn during update; otherwise, fill with BG_COLOR.
        if not self.bg_img:
            screen.fill(BG_COLOR)
        # Load and draw the logo if not already loaded.
        if self.logo_img is None:
            try:
                # Load the logo image.
                logo = pygame.image.load(resource_path("images/logo.png")).convert_alpha()
                # Expand the logo: scale it by a factor of 2 (or adjust as needed).
                self.logo_img = pygame.transform.scale(logo, (logo.get_width() * 2, logo.get_height() * 2))
            except Exception as e:
                print("Error loading logo:", e)
                self.logo_img = pygame.Surface((200, 100), pygame.SRCALPHA)
                pygame.draw.rect(self.logo_img, (255, 255, 255, 180), self.logo_img.get_rect())

        if self.logo_img:
            logo_x = (screen.get_width() - self.logo_img.get_width()) // 2
            logo_y = int(30 * self.scale_y)
            screen.blit(self.logo_img, (logo_x, logo_y))
        # Draw the buttons.
        draw_button(screen, self.scaled_buttons["manual"], "Manual Mode", self.font, color=(0, 100, 180))
        draw_button(screen, self.scaled_buttons["auto"], "Automatic Mode", self.font, color=(0, 100, 180))
        draw_button(screen, self.scaled_buttons["exit"], "Exit", self.font, color=(0, 100, 180))

    def get_next_state(self):
        """
        Retrieves the next state for the application, if a state transition was requested.

        Returns:
            Object or None: The next state instance, or None if no transition is needed.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
