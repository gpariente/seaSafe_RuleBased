# states/simulation_ui.py
"""
Simulation UI State Module

This module defines the SimulationState class, which is responsible for running and rendering
the main simulation. It sets up the simulation layout (grid, minimap, UI panel, etc.), handles
user events (e.g., pause/resume, replay, compare, state transitions), updates the simulation by
stepping through the collision avoidance algorithm, and renders the simulation (including ships,
trails, safety circles, and grid labels) onto the screen.

"""

import pygame
from config import BASE_RESOLUTIONS, LEFT_MARGIN, TOP_MARGIN, BOTTOM_MARGIN, UI_PANEL_HEIGHT, BG_COLOR
from draw_utils import (draw_grid, draw_ship_trail, draw_safety_circle, draw_ship_rect,
                        draw_star, draw_y_axis_labels_in_margin, draw_x_axis_labels_in_margin,
                        draw_dashed_line, draw_button)
from simulator import Simulator
from ship import Ship

class SimulationState:
    def __init__(self, screen, scenario_data=None):
        """
        Initializes the SimulationState.

        Parameters:
            screen (pygame.Surface): The main display surface.
            scenario_data (dict, optional): A dictionary containing the simulation parameters
                (e.g., map_size, safe_distance, heading_range, heading_step, time_step, ships).
                If not provided, an empty dictionary is used.
        
        The state maintains:
          - A reference to the Simulator instance (created when first needed).
          - Flags for pause/resume, scenario completion, and compare mode.
          - Layout parameters computed based on the current window size.
          - Background scrolling variables.
        """
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["simulation"]
        self.next_state = None
        self.scenario_data = scenario_data if scenario_data is not None else {}
        self.sim = None           # Simulator instance; created when needed.
        self.paused = False       # Flag to pause/resume simulation.
        self.scenario_finished = False  # Flag indicating if all ships have reached their destination.
        self.compare_mode = False  # Flag to toggle drawing of dashed lines for original routes.
        self.sea_scroll_x = 0.0   # Horizontal scroll offset for the sea background.
        self.sea_scroll_speed = 30.0  # Scrolling speed in pixels per second.

    def handle_events(self, events):
        """
        Processes user input events (mouse and keyboard) for the simulation state.

        - Mouse clicks on various UI buttons trigger state transitions:
            - Back: Return to the Main Menu.
            - Replay: Restart the current simulation.
            - Compare: Toggle compare mode to draw dashed lines for original ship paths.
            - Next: Transition to the Stats state (if the scenario is finished).
        - The space bar toggles pause/resume of the simulation.

        Parameters:
            events (list): A list of Pygame events.
        """
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                # If the "Back" button is clicked, return to the main menu and reset simulation variables.
                if self.btn_back_sim.collidepoint(event.pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
                    self.sim = None
                    self.paused = False
                    self.scenario_finished = False
                    self.compare_mode = False
                # If the "Replay" button is clicked, restart the simulation.
                elif self.btn_replay_sim.collidepoint(event.pos):
                    self.sim = None
                    self.paused = False
                    self.scenario_finished = False
                    self.compare_mode = False
                # Toggle compare mode if the "Compare" button is clicked and scenario is finished.
                elif self.btn_compare.collidepoint(event.pos) and self.scenario_finished:
                    self.compare_mode = not self.compare_mode
                # Transition to the Stats state if "Next" is clicked and scenario is finished.
                elif self.btn_next.collidepoint(event.pos) and self.scenario_finished:
                    from states.stats import StatsState
                    self.next_state = StatsState(self.screen, self, self.scenario_data)
            elif event.type == pygame.KEYDOWN:
                # Toggle pause/resume when space bar is pressed.
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused

    def update(self, dt):
        """
        Updates the simulation state for the current time step.

        This includes:
          - Scaling and layout: Calculates the scale factor based on the current window size,
            determines the simulation area, margins, and positions of UI elements (buttons).
          - Creating the Simulator instance if it is not already created using the provided scenario data.
          - Advancing the simulation (if not paused) by executing one simulation step.
          - Recording each ship's trail for display purposes.
          - Checking if all ships have reached their destination.

        Parameters:
            dt (float): Elapsed time in seconds since the last update.
        """
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        self.scale = min(current_w / base_w, current_h / base_h)
        self.sim_area_w = int(base_w * self.scale)
        self.sim_area_h = int(base_h * self.scale)
        self.offset_sim_x = (current_w - self.sim_area_w) // 2
        self.offset_sim_y = (current_h - self.sim_area_h) // 2

        # Calculate scaled margins and UI panel parameters.
        self.left_margin = int(LEFT_MARGIN * self.scale)
        self.top_margin = int(TOP_MARGIN * self.scale)
        self.map_width = int(800 * self.scale)
        self.map_height = int(800 * self.scale)
        self.bottom_margin = int(BOTTOM_MARGIN * self.scale)
        self.ui_panel_height = int(UI_PANEL_HEIGHT * self.scale)
        self.ui_panel_y = self.offset_sim_y + self.top_margin + self.map_height + self.bottom_margin

        # Define positions for UI buttons on the simulation panel.
        self.btn_back_sim = pygame.Rect(self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                          self.ui_panel_y + int(5 * self.scale),
                                          int(100 * self.scale), int(35 * self.scale))
        self.btn_replay_sim = pygame.Rect(self.offset_sim_x + self.left_margin + int(120 * self.scale),
                                          self.ui_panel_y + int(5 * self.scale),
                                          int(100 * self.scale), int(35 * self.scale))
        self.btn_compare = pygame.Rect(self.offset_sim_x + self.left_margin + int(230 * self.scale),
                                       self.ui_panel_y + int(5 * self.scale),
                                       int(100 * self.scale), int(35 * self.scale))
        self.btn_next = pygame.Rect(self.offset_sim_x + self.left_margin + int(340 * self.scale),
                                    self.ui_panel_y + int(5 * self.scale),
                                    int(100 * self.scale), int(35 * self.scale))
    
        # Create the Simulator instance if it does not exist.
        if self.sim is None:
            ships = []
            ship_datas = self.scenario_data.get("ships")
            if not ship_datas:
                # Provide default ship data if none is provided.
                ship_datas = [{
                    "name": "Ship1", "heading": 0.0, "speed": 20.0,
                    "start_x": 0.0, "start_y": 0.0, "dest_x": 5.0, "dest_y": 5.0,
                    "length_m": 300, "width_m": 50
                }]
            ship_colors = [(0, 255, 0), (255, 255, 0), (128, 128, 128), (0, 0, 0), (128, 0, 128)]
            for i, sdata in enumerate(ship_datas):
                sname = sdata.get("name", f"Ship{i+1}")
                heading = sdata.get("heading", 0.0)
                speed = sdata.get("speed", 20.0)
                sx = sdata.get("start_x", 0.0)
                sy = sdata.get("start_y", 0.0)
                dx_ = sdata.get("dest_x", 5.0)
                dy_ = sdata.get("dest_y", 5.0)
                length_ = sdata.get("length_m", 300)
                width_ = sdata.get("width_m", 50)
                from ship import Ship
                ship = Ship(sname, sx, sy, heading, speed, dx_, dy_, length_, width_)
                # Assign a color to the ship based on its index.
                ship.color = ship_colors[i % len(ship_colors)]
                ship.trail = []  # Initialize an empty trail for the ship.
                ship.source_x = sx  # Store the source x-coordinate.
                ship.source_y = sy  # Store the source y-coordinate.
                ships.append(ship)
            from simulator import Simulator
            self.sim = Simulator(
                ships=ships,
                time_step=self.scenario_data.get("time_step", 30),
                safe_distance=self.scenario_data.get("safe_distance", 0.2),
                heading_search_range=self.scenario_data.get("heading_range", 40),
                heading_search_step=self.scenario_data.get("heading_step", 1)
            )
            # Ensure that "map_size" is set in the scenario data.
            self.scenario_data.setdefault("map_size", 6.0)
            self.scenario_finished = False
            self.paused = False
            self.compare_mode = False

        # If the simulation is not finished and not paused, perform a simulation step.
        if not self.scenario_finished and not self.paused:
            self.sim.step(debug=False)
            # Append the current position of each ship to its trail.
            for sh in self.sim.ships:
                sh.trail.append((sh.x, sh.y))
            # Check if all ships have reached their destination.
            if self.sim.all_ships_arrived():
                self.scenario_finished = True

    def render(self, screen):
        """
        Renders the simulation UI, including the map grid, ships with trails and safety circles,
        destination markers, time step indicator, pause message, coordinate axis labels, and UI panel.

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        screen.fill(BG_COLOR)
        # Define the simulation area rectangle.
        simulation_area_rect = pygame.Rect(self.offset_sim_x, self.offset_sim_y, self.sim_area_w, self.sim_area_h)
        pygame.draw.rect(screen, BG_COLOR, simulation_area_rect)
        # Define the map rectangle within the simulation area.
        map_rect = pygame.Rect(self.offset_sim_x + self.left_margin,
                               self.offset_sim_y + self.top_margin,
                               self.map_width, self.map_height)
        # Create a scaled font for simulation display.
        sim_font = pygame.font.SysFont(None, int(28 * self.scale))
        # Calculate the conversion factor from Nautical Miles to pixels.
        nm_to_px = self.map_width / self.scenario_data.get("map_size", 6.0)
        from draw_utils import draw_grid, draw_ship_trail, draw_safety_circle, draw_ship_rect, draw_star
        # Draw the grid over the map.
        draw_grid(screen, map_rect, self.scenario_data.get("map_size", 6.0), nm_to_px, tick_step=0.5)
        # Draw each ship's trail, safety circle, and ship rectangle.
        for s in self.sim.ships:
            draw_ship_trail(screen, s, nm_to_px, self.map_height,
                            offset_x=self.offset_sim_x + self.left_margin,
                            offset_y=self.offset_sim_y + self.top_margin)
            draw_safety_circle(screen, s, self.sim.safe_distance, nm_to_px, self.map_height,
                               offset_x=self.offset_sim_x + self.left_margin,
                               offset_y=self.offset_sim_y + self.top_margin)
            draw_ship_rect(screen, s, nm_to_px, self.map_height,
                           offset_x=self.offset_sim_x + self.left_margin,
                           offset_y=self.offset_sim_y + self.top_margin)
        # Draw destination markers (stars) for each ship.
        for s in self.sim.ships:
            dest_x_screen = self.offset_sim_x + self.left_margin + int(s.dest_x * nm_to_px)
            dest_y_screen = self.offset_sim_y + self.top_margin + self.map_height - int(s.dest_y * nm_to_px)
            draw_star(screen, (dest_x_screen, dest_y_screen), int(8 * self.scale), s.color)
        
        # Display the current simulation time.
        time_label = sim_font.render(f"Current Time Step: {self.sim.current_time}s", True, (0, 0, 0))
        screen.blit(time_label, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                 self.offset_sim_y + self.top_margin + int(10 * self.scale)))
        # Display instruction to pause/resume the simulation.
        space_label = sim_font.render("Press SPACE to Pause/Resume", True, (200, 0, 0))
        screen.blit(space_label, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                  self.offset_sim_y + self.top_margin + int(30 * self.scale)))
        # If the simulation is paused, display a pause message.
        if self.paused:
            pause_text = sim_font.render("PAUSED", True, (255, 0, 0))
            screen.blit(pause_text, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                     self.offset_sim_y + self.top_margin + int(50 * self.scale)))
        from draw_utils import draw_y_axis_labels_in_margin, draw_x_axis_labels_in_margin
        # Draw y-axis labels in the margin.
        draw_y_axis_labels_in_margin(screen,
            pygame.Rect(self.offset_sim_x, self.offset_sim_y + self.top_margin, self.left_margin, self.map_height),
            self.scenario_data.get("map_size", 6.0), sim_font, tick_step=0.5)
        # Draw x-axis labels in the margin.
        draw_x_axis_labels_in_margin(screen,
            pygame.Rect(self.offset_sim_x + self.left_margin, self.offset_sim_y + self.top_margin + self.map_height, self.map_width, BOTTOM_MARGIN),
            self.scenario_data.get("map_size", 6.0), sim_font, tick_step=0.5)
        # Draw a horizontal line separating the map from the UI panel.
        pygame.draw.line(screen, (200, 200, 200),
                         (self.offset_sim_x + self.left_margin, self.offset_sim_y + self.top_margin + self.map_height),
                         (self.offset_sim_x + self.left_margin + self.map_width, self.offset_sim_y + self.top_margin + self.map_height),
                         1)
        # Draw the UI panel.
        ui_panel_rect = pygame.Rect(self.offset_sim_x + self.left_margin, self.ui_panel_y, self.map_width, self.ui_panel_height)
        pygame.draw.rect(screen, (60, 60, 60), ui_panel_rect)
        # Draw UI panel buttons.
        draw_button(screen, self.btn_back_sim, "Back", sim_font)
        draw_button(screen, self.btn_replay_sim, "Replay", sim_font)
        if self.scenario_finished:
            # If compare mode is enabled, draw dashed lines representing original ship paths.
            if self.compare_mode:
                from draw_utils import draw_dashed_line
                for s in self.sim.ships:
                    start_pos = (self.offset_sim_x + self.left_margin + int(s.source_x * nm_to_px),
                                 self.offset_sim_y + self.top_margin + self.map_height - int(s.source_y * nm_to_px))
                    end_pos = (self.offset_sim_x + self.left_margin + int(s.dest_x * nm_to_px),
                               self.offset_sim_y + self.top_margin + self.map_height - int(s.dest_y * nm_to_px))
                    draw_dashed_line(screen, s.color, start_pos, end_pos, dash_length=int(5*self.scale), space_length=int(10*self.scale))
            else:
                # If compare mode is not enabled, display a finish message.
                finish_text = sim_font.render("Scenario finished - all ships reached destinations!", True, (0, 150, 0))
                fx = self.offset_sim_x + self.left_margin + (self.map_width - finish_text.get_width()) // 2
                fy = self.offset_sim_y + self.top_margin + self.map_height // 2 - finish_text.get_height() // 2
                screen.blit(finish_text, (fx, fy))
            # Draw the "Compare" and "Next" buttons in the UI panel.
            draw_button(screen, self.btn_compare, "Compare", sim_font)
            draw_button(screen, self.btn_next, "Next", sim_font)
    
    def get_next_state(self):
        """
        Retrieves the next state for the application and resets the next_state variable.

        Returns:
            Object or None: The next state instance if a transition is requested; otherwise, None.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
