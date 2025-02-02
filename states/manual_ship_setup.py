# states/manual_ship_setup.py
"""
Manual Ship Setup State Module

This module defines the ManualShipSetupState class used for configuring individual ship parameters
in a manually defined scenario. In this state, users specify each ship’s speed, starting coordinates,
destination coordinates, length, and width. The inputs are validated against defined criteria (e.g.,
speed ≤ 50, length ≤ 800, width ≤ 200, and coordinates within the map). A minimap is displayed to help
visualize the ship positions.

"""

import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from ui_component import TextBox
from draw_utils import draw_button, draw_minimap, draw_scrolling_bg
import math

def create_ship_boxes(num, font):
    """
    Creates a list of rows, each row containing TextBox instances for ship parameters.
    
    Parameters:
        num (int): The number of ships.
        font (pygame.font.Font): The font to use for rendering text in the textboxes.
    
    Returns:
        list: A list of lists; each sublist contains five TextBox objects corresponding to:
              [speed, start(x,y), destination(x,y), length, width]
    """
    ship_boxes = []
    start_y = 150
    for i in range(num):
        row = []
        # Index 0: speed, index 1: start position, index 2: destination position,
        # index 3: ship length, index 4: ship width.
        row.append(TextBox((80, start_y, 80, 30), font, "20"))
        row.append(TextBox((180, start_y, 100, 30), font, "0,4"))
        row.append(TextBox((300, start_y, 100, 30), font, "8,4"))
        row.append(TextBox((420, start_y, 80, 30), font, "400"))
        row.append(TextBox((520, start_y, 80, 30), font, "100"))
        ship_boxes.append(row)
        start_y += 60  # Increase y position for the next ship row.
    return ship_boxes

class ManualShipSetupState:
    def __init__(self, screen, scenario_data):
        """
        Initializes the Manual Ship Setup state.

        Parameters:
            screen (pygame.Surface): The main display surface.
            scenario_data (dict): Dictionary containing scenario parameters (e.g., map size).
        """
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["manual_ship_setup"]
        self.scenario_data = scenario_data
        # Create textboxes for each ship based on the number of ships.
        self.ship_boxes = create_ship_boxes(scenario_data["num_ships"], self.font)
        self.next_state = None
        
        # Define navigation buttons.
        self.buttons = {
            "back": pygame.Rect(50, 600, 120, 40),
            "start": pygame.Rect(250, 600, 120, 40)
        }
        
        # For moving background.
        self.bg_img = None
        self.bg_scroll_x = 0.0
        self.last_dt = 0.0
        
        # String to hold any validation warning messages.
        self.warning_msg = ""

    def validate_inputs(self):
        """
        Validates the ship setup data from the textboxes.
        
        Validation rules:
            - All fields must be non-empty.
            - All numeric values must be positive.
            - Speed must be > 0 and ≤ 50.
            - Ship length must be > 0 and ≤ 800.
            - Ship width must be > 0 and ≤ 200.
            - Start and destination fields must contain two comma-separated numbers,
              each within the range [0, scenario_data["map_size"]].
        
        Returns:
            tuple: (is_valid (bool), message (str))
                   If valid, returns (True, "").
                   Otherwise, returns (False, <error message>).
        """
        map_size = self.scenario_data.get("map_size", 6.0)
        for i, row in enumerate(self.ship_boxes):
            # Validate speed (index 0)
            speed_str = row[0].get_str()
            if speed_str == "":
                return (False, f"Ship {i+1}: Please fill in the speed.")
            try:
                speed = float(speed_str)
            except ValueError:
                return (False, f"Ship {i+1}: Invalid numeric value for speed.")
            if speed <= 0 or speed > 50:
                return (False, f"Ship {i+1}: Speed must be > 0 and <= 50.")
            
            # Validate start position (index 1)
            start_str = row[1].get_str()
            if start_str == "":
                return (False, f"Ship {i+1}: Please fill in the start position.")
            try:
                parts = [float(x) for x in start_str.split(',')]
            except ValueError:
                return (False, f"Ship {i+1}: Invalid numeric value in start position.")
            if len(parts) != 2:
                return (False, f"Ship {i+1}: Start position must have two numbers separated by a comma.")
            sx, sy = parts
            if sx < 0 or sy < 0 or sx > map_size or sy > map_size:
                return (False, f"Ship {i+1}: Start position must be within [0, {map_size}].")
            
            # Validate destination (index 2)
            dest_str = row[2].get_str()
            if dest_str == "":
                return (False, f"Ship {i+1}: Please fill in the destination.")
            try:
                parts = [float(x) for x in dest_str.split(',')]
            except ValueError:
                return (False, f"Ship {i+1}: Invalid numeric value in destination.")
            if len(parts) != 2:
                return (False, f"Ship {i+1}: Destination must have two numbers separated by a comma.")
            dx, dy = parts
            if dx < 0 or dy < 0 or dx > map_size or dy > map_size:
                return (False, f"Ship {i+1}: Destination must be within [0, {map_size}].")
            
            # Validate ship length (index 3)
            length_str = row[3].get_str()
            if length_str == "":
                return (False, f"Ship {i+1}: Please fill in the ship length.")
            try:
                length_val = float(length_str)
            except ValueError:
                return (False, f"Ship {i+1}: Invalid numeric value for ship length.")
            if length_val <= 0 or length_val > 800:
                return (False, f"Ship {i+1}: Ship length must be > 0 and <= 800.")
            
            # Validate ship width (index 4)
            width_str = row[4].get_str()
            if width_str == "":
                return (False, f"Ship {i+1}: Please fill in the ship width.")
            try:
                width_val = float(width_str)
            except ValueError:
                return (False, f"Ship {i+1}: Invalid numeric value for ship width.")
            if width_val <= 0 or width_val > 200:
                return (False, f"Ship {i+1}: Ship width must be > 0 and <= 200.")
        return (True, "")

    def handle_events(self, events):
        """
        Processes Pygame events for the manual ship setup state.

        - If the Back button is clicked, transitions back to the Manual Scenario state.
        - If the Start button is clicked, validates the ship input data:
            - If valid, builds the ship data, updates the scenario data, and transitions to the Simulation state.
            - If invalid, sets a warning message that will be displayed.
        - Passes events to each textbox for text input handling.

        Parameters:
            events (list): List of Pygame events.
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.scaled_buttons["back"].collidepoint(event.pos):
                    from states.manual_scenario import ManualScenarioState
                    self.next_state = ManualScenarioState(self.screen)
                elif self.scaled_buttons["start"].collidepoint(event.pos):
                    valid, msg = self.validate_inputs()
                    if not valid:
                        self.warning_msg = msg
                    else:
                        self.warning_msg = ""
                        ships = []
                        for i, row in enumerate(self.ship_boxes):
                            speed = float(row[0].get_str())
                            sx, sy = map(float, row[1].get_str().split(','))
                            dx, dy = map(float, row[2].get_str().split(','))
                            length_val = float(row[3].get_str())
                            width_val = float(row[4].get_str())
                            # Compute the heading toward destination if the ship is not already at the destination.
                            heading = math.degrees(math.atan2(dy - sy, dx - sx)) if (dx, dy) != (sx, sy) else 0.0
                            ship_data = {
                                "name": f"Ship{i+1}",
                                "heading": heading,
                                "speed": speed,
                                "start_x": sx,
                                "start_y": sy,
                                "dest_x": dx,
                                "dest_y": dy,
                                "length_m": length_val,
                                "width_m": width_val
                            }
                            ships.append(ship_data)
                        # Add ship data to the scenario data.
                        self.scenario_data["ships"] = ships
                        from states.simulation_ui import SimulationState
                        self.next_state = SimulationState(self.screen, self.scenario_data)
            # Forward event handling to each textbox.
            for row in self.ship_boxes:
                for tb in row:
                    tb.handle_event(event)

    def update(self, dt):
        """
        Updates the manual ship setup state, including scaling UI elements and loading the background.

        Parameters:
            dt (float): Elapsed time in seconds since the last update.
        """
        self.last_dt = dt
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
        # Update textboxes' rectangles.
        for row in self.ship_boxes:
            for tb in row:
                tb.update_rect(self.scale_x, self.scale_y)
        # Load background image if not already loaded.
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None

    def render(self, screen):
        """
        Renders the manual ship setup UI, including background, header, ship input rows,
        navigation buttons, a minimap, and any validation warning messages.

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        # Draw the scrolling background.
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, self.last_dt)
        else:
            screen.fill(BG_COLOR)
        # Draw header text.
        header = self.font.render("Speed | Start(x,y) | Dest(x,y) | Length(m) | Width(m)", True, (255,255,255))
        screen.blit(header, (80 * self.scale_x, 90 * self.scale_y))
        # Draw ship input rows.
        y = 150
        for i, row in enumerate(self.ship_boxes):
            ship_label = self.font.render(f"Ship {i+1}", True, (255,255,255))
            screen.blit(ship_label, (10 * self.scale_x, y * self.scale_y + 10 * self.scale_y))
            for tb in row:
                tb.draw(screen)
            y += 60
        # Draw navigation buttons.
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font, color=(0,100,180))
        draw_button(screen, self.scaled_buttons["start"], "Start", self.font, color=(0,100,180))
        # Draw a minimap (dummy version) showing ship source and destination points.
        dummy_ships = []
        ship_colors = [(0,255,0), (255,255,0), (128,128,128), (0,0,0), (128,0,128)]
        for i, row in enumerate(self.ship_boxes):
            try:
                sx, sy = map(float, row[1].get_str().split(','))
            except:
                sx, sy = 0.0, 0.0
            try:
                dx, dy = map(float, row[2].get_str().split(','))
            except:
                dx, dy = 5.0, 5.0
            dummy_ship = type("DummyShip", (), {})()
            dummy_ship.x = sx
            dummy_ship.y = sy
            dummy_ship.dest_x = dx
            dummy_ship.dest_y = dy
            dummy_ship.color = ship_colors[i % len(ship_colors)]
            dummy_ships.append(dummy_ship)
        draw_minimap(screen, dummy_ships, self.scenario_data["map_size"],
                     (700 * self.scale_x, 20 * self.scale_y), int(140 * self.scale_x))
        # Draw any warning message under the button area (e.g., 20 pixels below the buttons).
        if self.warning_msg:
            warning = self.font.render(self.warning_msg, True, (255, 0, 0))
            screen.blit(warning, (300 * self.scale_x, (600 * self.scale_y) + 50))
    
    def get_next_state(self):
        """
        Retrieves the next state (if any) and resets the next_state variable.

        Returns:
            Object or None: The next state instance if a transition is requested; otherwise, None.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
