# states/stats.py
"""
Stats State Module

This module defines the StatsState class, which displays simulation insights after the scenario
has finished running. The stats screen shows:
  - Total simulation time.
  - Per-ship insights: each ship's actual travel time (recorded when the ship reaches its destination),
    the optimal time (discretized to the simulation time step) if the ship had traveled in a straight line,
    and the extra time incurred.
  - Encounter classification counts (head-on, crossing, overtaking).
  - Overall ship performance metrics (average, minimum, and maximum extra time).
  - A professional bar chart comparing optimal versus actual travel times.
  
The screen supports vertical scrolling via keyboard arrow keys and mouse wheel.
Users can navigate back to the simulation screen or return to the main menu.
"""

import pygame
from config import BASE_RESOLUTIONS, BG_COLOR
from draw_utils import draw_button
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io

# Mapping from common RGB tuples to color names.
color_names = {
    (0, 255, 0): "Green",
    (255, 255, 0): "Yellow",
    (128, 128, 128): "Gray",
    (0, 0, 0): "Black",
    (128, 0, 128): "Purple"
}

def draw_time_comparison_chart(screen, x, y, width, height, ship_data, timestep, font):
    """
    Draws a professional bar chart comparing optimal time and actual travel time for each ship,
    using matplotlib. The optimal times are discretized to the simulation time step.

    Parameters:
        screen (pygame.Surface): The target surface.
        x, y (int): Top-left coordinates for the chart area.
        width, height (int): Dimensions of the chart area.
        ship_data (list of dict): Each dict must contain:
            - 'label': Ship label (e.g., "Green")
            - 'optimal': Optimal time in seconds.
            - 'actual': Actual travel time in seconds.
        timestep (float): Simulation time step in seconds, used to discretize optimal times.
        font (pygame.font.Font): Font used for rendering text labels.
    """
    n = len(ship_data)
    if n == 0:
        return

    # Discretize optimal times: round up to the nearest simulation timestep.
    optimal_times = [math.ceil(data['optimal'] / timestep) * timestep for data in ship_data]
    actual_times = [data['actual'] for data in ship_data]
    labels = [data['label'] for data in ship_data]

    x_indices = np.arange(n)
    bar_width = 0.35

    dpi = 100
    fig_width = width / dpi
    fig_height = height / dpi

    fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=dpi)
    rects1 = ax.bar(x_indices - bar_width/2, optimal_times, bar_width, label='Optimal', color='lightgray')
    rects2 = ax.bar(x_indices + bar_width/2, actual_times, bar_width, label='Actual', color='green')

    ax.set_ylabel('Time (s)')
    ax.set_title('Optimal vs Actual Travel Times')
    ax.set_xticks(x_indices)
    ax.set_xticklabels(labels)

    fig.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close(fig)
    chart_image = pygame.image.load(buf)
    chart_image = pygame.transform.scale(chart_image, (width, height))
    screen.blit(chart_image, (x, y))

class StatsState:
    def __init__(self, screen, sim_state, scenario_data):
        """
        Initializes the StatsState.

        Parameters:
            screen (pygame.Surface): The main display surface.
            sim_state (SimulationState): The SimulationState instance that holds the finished simulation.
            scenario_data (dict): Dictionary containing the simulation parameters.
        
        This state stores a reference to the Simulator (via sim_state.sim) and prepares variables
        for rendering the simulation statistics.
        """
        self.screen = screen
        self.sim_state = sim_state  # Preserves the finished simulation run
        self.sim = sim_state.sim    # Simulator instance containing simulation data and counters
        self.scenario_data = scenario_data
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["stats"]
        self.next_state = None
        self.scroll_offset = 0  # Vertical scroll offset (in pixels) for content rendering
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
                if event.button == 4:  # Mouse wheel up
                    self.scroll_offset = max(0, self.scroll_offset - 20)
                elif event.button == 5:  # Mouse wheel down
                    self.scroll_offset += 20
                else:
                    pos = event.pos
                    if self.btn_back_stats.collidepoint(pos):
                        self.next_state = self.sim_state
                    elif self.btn_main_menu.collidepoint(pos):
                        from states.main_menu import MainMenuState
                        self.next_state = MainMenuState(self.screen)
    
    def update(self, dt):
        """
        Updates the stats screen state.

        This method positions the navigation buttons relative to the current window dimensions.
        The Back button is anchored at the bottom left and the Main Menu button at the bottom right.

        Parameters:
            dt (float): Elapsed time in seconds since the last update (unused in this state).
        """
        current_w, current_h = self.screen.get_size()
        self.btn_back_stats = pygame.Rect(50, current_h - 60, 120, 40)
        self.btn_main_menu = pygame.Rect(current_w - 170, current_h - 60, 120, 40)
    
    def render(self, screen):
        """
        Renders the stats screen.

        This includes:
          - Filling the background.
          - Creating a list of content lines with simulation insights:
            * Total simulation time.
            * For each ship: actual arrival time, optimal time (discretized to the simulation time step), and extra time.
            * Overall ship performance metrics (average, min, max extra time).
            * Encounter classification counts.
          - Rendering the text content with vertical scrolling.
          - Drawing a professional bar chart comparing optimal vs. actual travel times.
          - Drawing the navigation buttons (Back and Main Menu).

        Parameters:
            screen (pygame.Surface): The display surface.
        """
        screen.fill(BG_COLOR)
        content_lines = []
        content_lines.append(f"Total Simulation Time: {self.sim.current_time:.1f} s")
        content_lines.append("")
        
        total_extra_time = 0
        delays = []
        ship_chart_data = []  # Data for bar chart
        # Per-ship insights.
        for ship in self.sim.ships:
            ship_color = tuple(ship.color)
            ship_label = color_names.get(ship_color, "Unknown")
            dx = ship.dest_x - ship.source_x
            dy = ship.dest_y - ship.source_y
            distance = (dx**2 + dy**2)**0.5
            # Compute optimal time and discretize it to the simulation time step.
            raw_optimal = (distance / ship.speed * 3600) if ship.speed > 0 else 0
            timestep = self.sim.time_step  # Use the simulation time step.
            optimal_time = math.ceil(raw_optimal / timestep) * timestep
            # Actual time: use the recorded arrival_time if available; otherwise, use current simulation time.
            actual_time = ship.arrival_time if ship.arrival_time is not None else self.sim.current_time
            extra_time = actual_time - optimal_time
            delays.append(extra_time)
            total_extra_time += extra_time
            content_lines.append(f"{ship_label}:")
            content_lines.append(f"  Actual Time: {actual_time:.1f} s")
            content_lines.append(f"  Optimal Time: {optimal_time:.1f} s")
            content_lines.append(f"  Extra Time: {extra_time:.1f} s")
            content_lines.append("")
            ship_chart_data.append({
                "label": ship_label,
                "optimal": optimal_time,
                "actual": actual_time
            })

        if delays:
            avg_delay = sum(delays) / len(delays)
            min_delay = min(delays)
            max_delay = max(delays)
            content_lines.append("Overall Ship Performance:")
            content_lines.append(f"  Average Extra Time: {avg_delay:.1f} s")
            content_lines.append(f"  Minimum Extra Time: {min_delay:.1f} s")
            content_lines.append(f"  Maximum Extra Time: {max_delay:.1f} s")
            content_lines.append("")
        
        # Encounter classification counts.
        # content_lines.append("Encounter Classifications:")
        # content_lines.append(f"  Head-on: {self.sim.count_headon}")
        # content_lines.append(f"  Crossing: {self.sim.count_crossing}")
        # content_lines.append(f"  Overtaking: {self.sim.count_overtaking}")
        # content_lines.append("")
        
        # Overall maneuvers.
        total_maneuvers = self.sim.count_headon + self.sim.count_crossing + self.sim.count_overtaking
        content_lines.append(f"Total Maneuvers: {total_maneuvers}")
        content_lines.append("")
        
        # Render text content with vertical scrolling.
        x_start = 20  # Provide more horizontal space.
        y_text = 50 - self.scroll_offset
        for line in content_lines:
            text = self.font.render(line, True, (255, 255, 255))
            screen.blit(text, (x_start, y_text))
            y_text += self.line_height
        
        # Draw bar chart below the text.
        chart_x = x_start
        chart_y = y_text + 20
        chart_width = self.screen.get_width() - 40  # Leave a margin.
        chart_height = 150  # Fixed height for the chart.
        draw_time_comparison_chart(screen, chart_x, chart_y, chart_width, chart_height, ship_chart_data, timestep, self.font)
        
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
