# states/manual_scenario.py
"""
Manual Scenario State Module

This module defines the ManualScenarioState class which implements the first step of the manual
scenario setup. In this state, users input the simulation environment parameters (such as map size,
safety zone, heading range, heading step, time step, and number of ships). The inputs are validated
according to specified rules before proceeding to the Manual Ship Setup state.


"""

import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from ui_component import TextBox
from draw_utils import draw_button, draw_scrolling_bg
from states.manual_ship_setup import ManualShipSetupState

class ManualScenarioState:
    def __init__(self, screen):
        """
        Initializes the ManualScenarioState.

        Parameters:
            screen (pygame.Surface): The main display surface.
        """
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["manual_scenario"]
        self.next_state = None
        
        # Create text boxes for scenario parameters with default values.
        self.box_map_size = TextBox((300, 100, 120, 30), self.font, "8")
        self.box_safe_dist = TextBox((300, 150, 120, 30), self.font, "0.2")
        self.box_search_rng = TextBox((300, 200, 120, 30), self.font, "20")
        self.box_search_step = TextBox((300, 250, 120, 30), self.font, "5")
        self.box_time_step = TextBox((300, 300, 120, 30), self.font, "30")
        self.box_num_ships = TextBox((300, 350, 120, 30), self.font, "2")
        self.text_boxes = [
            self.box_map_size,
            self.box_safe_dist,
            self.box_search_rng,
            self.box_search_step,
            self.box_time_step,
            self.box_num_ships
        ]
        
        # Define navigation buttons (Back and Next).
        self.buttons = {
            "back": pygame.Rect(50, 500, 100, 40),
            "next": pygame.Rect(600, 500, 100, 40)
        }
        
        # For moving background.
        self.bg_img = None
        self.bg_scroll_x = 0.0
        self.last_dt = 0.0
        
        # String to hold any validation warning messages.
        self.warning_msg = ""

    def validate_inputs(self):
        """
        Validates that each scenario parameter textbox is non-empty and contains a valid number,
        and that each value meets the specified constraints:
          - Map Size: positive and <= 20.
          - Safety Zone: positive.
          - Heading Range: positive and <= 90.
          - Heading Step: positive.
          - Time Step: positive.
          - #Ships: integer between 2 and 8.
        
        Returns:
            tuple: (is_valid (bool), message (str))
                   If valid, returns (True, ""). Otherwise, returns (False, <error message>).
        """
        # Ensure that no textbox is empty.
        for tb in self.text_boxes:
            if tb.get_str() == "":
                return (False, "Please fill all scenario data")
        # Validate and convert each value.
        try:
            map_size = float(self.box_map_size.get_str())
            if map_size <= 0 or map_size > 20:
                return (False, "Map Size must be > 0 and <= 20")
            safe_zone = float(self.box_safe_dist.get_str())
            if safe_zone <= 0:
                return (False, "Safety Zone must be positive")
            heading_range = float(self.box_search_rng.get_str())
            if heading_range <= 0 or heading_range > 90:
                return (False, "Heading Range must be > 0 and <= 90")
            heading_step = float(self.box_search_step.get_str())
            if heading_step <= 0:
                return (False, "Heading Step must be positive")
            time_step = float(self.box_time_step.get_str())
            if time_step <= 0:
                return (False, "Time Step must be positive")
            num_ships = int(self.box_num_ships.get_str())
            if num_ships < 2 or num_ships > 8:
                return (False, "#Ships must be between 2 and 8")
        except ValueError:
            return (False, "Invalid numeric value in scenario data")
        return (True, "")

    def handle_events(self, events):
        """
        Processes Pygame events for the manual scenario state.

        - If the Back button is clicked, transitions to the Main Menu state.
        - If the Next button is clicked, validates the inputs. If valid, transitions to the
          Manual Ship Setup state; otherwise, displays a warning message.
        - Also forwards events to each textbox for handling text input.

        Parameters:
            events (list): List of Pygame events.
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # Check if the Back button was clicked.
                if self.scaled_buttons["back"].collidepoint(event.pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
                # Check if the Next button was clicked.
                elif self.scaled_buttons["next"].collidepoint(event.pos):
                    valid, msg = self.validate_inputs()
                    if not valid:
                        self.warning_msg = msg
                    else:
                        self.warning_msg = ""
                        # Build the scenario_data dictionary from input values.
                        scenario_data = {
                            "map_size": float(self.box_map_size.get_str()),
                            "safe_distance": float(self.box_safe_dist.get_str()),
                            "heading_range": float(self.box_search_rng.get_str()),
                            "heading_step": float(self.box_search_step.get_str()),
                            "time_step": float(self.box_time_step.get_str()),
                            "num_ships": int(self.box_num_ships.get_str())
                        }
                        self.scenario_data = scenario_data
                        self.next_state = ManualShipSetupState(self.screen, scenario_data)
            # Forward the event to each textbox for text input.
            for tb in self.text_boxes:
                tb.handle_event(event)

    def update(self, dt):
        """
        Updates the state of the manual scenario screen.

        This includes saving the elapsed time for background scrolling, scaling the UI elements
        based on the current window size, and loading the background image if necessary.

        Parameters:
            dt (float): Elapsed time in seconds since the last update.
        """
        self.last_dt = dt  # Save dt for use in render() for background scrolling.
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        self.scale_x = current_w / base_w
        self.scale_y = current_h / base_h
        
        # Scale button positions.
        self.scaled_buttons = {}
        for key, rect in self.buttons.items():
            self.scaled_buttons[key] = pygame.Rect(
                int(rect.x * self.scale_x),
                int(rect.y * self.scale_y),
                int(rect.width * self.scale_x),
                int(rect.height * self.scale_y)
            )
        # Update the rectangle for each textbox.
        for tb in self.text_boxes:
            tb.update_rect(self.scale_x, self.scale_y)
        # Load background image if not already loaded.
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None

    def render(self, screen):
        """
        Renders the manual scenario UI, including the scrolling background, labels,
        textboxes, buttons, and any validation warning message.

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        # Draw scrolling background.
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, self.last_dt)
        else:
            screen.fill(BG_COLOR)
        # Draw labels and textboxes.
        labels = ["Map Size:", "Safety Zone:", "Heading Range:", "Heading Step:", "Time Step:", "#Ships:"]
        for tb, label_text in zip(self.text_boxes, labels):
            label = self.font.render(label_text, True, (255, 255, 255))
            screen.blit(label, (tb.rect.x - label.get_width() - 5, tb.rect.y))
            tb.draw(screen)
        # Draw the Back and Next buttons.
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font, color=(0, 100, 180))
        draw_button(screen, self.scaled_buttons["next"], "Next", self.font, color=(0, 100, 180))
        # Display a warning message (if any) below the textboxes.
        if self.warning_msg:
            warning = self.font.render(self.warning_msg, True, (255, 0, 0))
            screen.blit(warning, (300 * self.scale_x, 400 * self.scale_y))

    def get_next_state(self):
        """
        Returns the next state if a transition was requested, and clears the next_state.

        Returns:
            Object or None: The next state instance or None if no state transition is requested.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
