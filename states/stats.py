# states/stats.py
"""
Stats State Module

This module defines the StatsState class, which displays simulation insights after the scenario
has finished running. The stats screen shows:
  - Total simulation time.
  - Per-ship insights: each ship's optimal time (if it had traveled in a straight line) and the extra
    time incurred due to collision avoidance maneuvers.
  - Encounter classification counts (head-on, crossing, overtaking).
  - Detailed collision avoidance events.
  
The screen supports vertical scrolling via keyboard arrow keys and mouse wheel.
Users can navigate back to the simulation screen or return to the main menu.
"""

import pygame
from config import BASE_RESOLUTIONS, BG_COLOR
from draw_utils import draw_button

# Mapping from common RGB tuples to color names.
color_names = {
    (0, 255, 0): "Green",
    (255, 255, 0): "Yellow",
    (128, 128, 128): "Gray",
    (0, 0, 0): "Black",
    (128, 0, 128): "Purple"
}

class StatsState:
    def __init__(self, screen, sim_state, scenario_data):
        """
        Initializes the StatsState.

        Parameters:
            screen (pygame.Surface): The main display surface.
            sim_state (SimulationState): The SimulationState instance that holds the finished simulation.
            scenario_data (dict): Dictionary containing the simulation parameters.
        
        The state stores a reference to the Simulator (via sim_state.sim) and prepares variables for
        rendering the simulation statistics.
        """
        self.screen = screen
        self.sim_state = sim_state  # The complete SimulationState instance (preserves the simulation run)
        self.sim = sim_state.sim    # The Simulator instance containing simulation data and counters
        self.scenario_data = scenario_data
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["stats"]
        self.next_state = None
        self.scroll_offset = 0  # Vertical scroll offset (in pixels) for content
        self.line_height = self.font.get_height() + 5  # Height for each line of text

    def handle_events(self, events):
        """
        Processes Pygame events for the stats screen.

        - UP/DOWN arrow keys (or mouse wheel) adjust the vertical scroll offset.
        - Mouse clicks on the Back button return to the simulation state.
        - Mouse clicks on the Main Menu button transition to the Main Menu state.

        Parameters:
            events (list): A list of Pygame events.
        """
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    self.scroll_offset += 20
                elif event.key == pygame.K_UP:
                    self.scroll_offset = max(0, self.scroll_offset - 20)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Handle mouse wheel scrolling.
                if event.button == 4:  # Mouse wheel up
                    self.scroll_offset = max(0, self.scroll_offset - 20)
                elif event.button == 5:  # Mouse wheel down
                    self.scroll_offset += 20
                else:
                    pos = event.pos
                    if self.btn_back_stats.collidepoint(pos):
                        # Return to the simulation state, preserving the simulation run.
                        self.next_state = self.sim_state
                    elif self.btn_main_menu.collidepoint(pos):
                        from states.main_menu import MainMenuState
                        self.next_state = MainMenuState(self.screen)
    
    def update(self, dt):
        """
        Updates the stats screen state.

        This method positions the navigation buttons relative to the current window size.
        The Back button is anchored at the bottom left and the Main Menu button at the bottom right.

        Parameters:
            dt (float): Elapsed time in seconds since the last update (unused in this state).
        """
        current_w, current_h = self.screen.get_size()
        # Anchor the Back button 50 pixels from the left and 60 pixels from the bottom.
        self.btn_back_stats = pygame.Rect(50, current_h - 60, 120, 40)
        # Anchor the Main Menu button 170 pixels from the right and 60 pixels from the bottom.
        self.btn_main_menu = pygame.Rect(current_w - 170, current_h - 60, 120, 40)
    
    def render(self, screen):
        """
        Renders the stats screen.

        This includes:
          - Filling the background.
          - Creating a list of content lines with simulation insights:
            * Total simulation time.
            * For each ship: optimal time and extra time.
            * Encounter classification counts.
            * Detailed collision avoidance event messages.
          - Rendering the content with vertical scrolling.
          - Drawing navigation buttons (Back and Main Menu).

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        screen.fill(BG_COLOR)
        content_lines = []
        # Display total simulation time.
        content_lines.append(f"Total Simulation Time: {self.sim.current_time:.1f} s")
        content_lines.append("")
        # Display per-ship insights.
        for ship in self.sim.ships:
            # Convert ship.color to a tuple to lookup a color name.
            ship_color = tuple(ship.color)
            ship_label = color_names.get(ship_color, "Unknown")
            dx = ship.dest_x - ship.source_x
            dy = ship.dest_y - ship.source_y
            distance = (dx**2 + dy**2)**0.5
            # Compute the optimal time (in seconds) based on a straight-line course.
            optimal_time = (distance / ship.speed * 3600) if ship.speed > 0 else 0
            extra_time = self.sim.current_time - optimal_time
            content_lines.append(f"{ship_label}:")
            content_lines.append(f"  Optimal Time: {optimal_time:.1f} s")
            content_lines.append(f"  Extra Time: {extra_time:.1f} s")
            content_lines.append("")
        # Display encounter classification counts.
        if hasattr(self.sim, "count_headon"):
            content_lines.append("Encounter Classifications:")
            content_lines.append(f"  Head-on: {self.sim.count_headon}")
            content_lines.append(f"  Crossing: {self.sim.count_crossing}")
            content_lines.append(f"  Overtaking: {self.sim.count_overtaking}")
            content_lines.append("")
        # Display detailed collision avoidance events.
        if hasattr(self.sim, "collisions_avoided") and self.sim.collisions_avoided:
            content_lines.append("Collision Avoidance Events:")
            for msg in self.sim.collisions_avoided:
                content_lines.append(f"  {msg}")
            content_lines.append("")
        
        # Render all content lines with vertical scrolling.
        y = 50 - self.scroll_offset  # Starting y position, adjusted by scroll offset.
        for line in content_lines:
            text = self.font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, y))
            y += self.line_height
        
        # Draw navigation buttons anchored at the bottom.
        draw_button(screen, self.btn_back_stats, "Back", self.font)
        draw_button(screen, self.btn_main_menu, "Main Menu", self.font)
    
    def get_next_state(self):
        """
        Retrieves and resets the next state transition request.

        Returns:
            Object or None: The next state instance if a transition is requested; otherwise, None.
        """
        next_state = self.next_state
        self.next_state = None
        return next_state
