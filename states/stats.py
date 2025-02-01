# states/stats.py
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
        sim_state: the SimulationState instance (with the Simulator inside) that holds the run.
        scenario_data: dictionary with the scenario parameters.
        """
        self.screen = screen
        self.sim_state = sim_state  # The complete SimulationState instance
        self.sim = sim_state.sim    # The Simulator instance
        self.scenario_data = scenario_data
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["stats"]
        self.next_state = None
        self.scroll_offset = 0  # vertical scroll offset (in pixels)
        self.line_height = self.font.get_height() + 5

    def handle_events(self, events):
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
                        # Return the stored simulation state (preserving the finished run)
                        self.next_state = self.sim_state
                    elif self.btn_main_menu.collidepoint(pos):
                        from states.main_menu import MainMenuState
                        self.next_state = MainMenuState(self.screen)
    
    def update(self, dt):
        # Position the Back button at the bottom left and Main Menu button at the bottom right.
        current_w, current_h = self.screen.get_size()
        self.btn_back_stats = pygame.Rect(50, current_h - 60, 120, 40)
        self.btn_main_menu = pygame.Rect(current_w - 170, current_h - 60, 120, 40)
    
    def render(self, screen):
        screen.fill(BG_COLOR)
        content_lines = []
        content_lines.append(f"Total Simulation Time: {self.sim.current_time:.1f} s")
        content_lines.append("")
        # Per-ship insights: show optimal time and extra time using ship color names.
        for ship in self.sim.ships:
            # Convert ship.color to tuple to look up a color name.
            ship_color = tuple(ship.color)
            ship_label = color_names.get(ship_color, "Unknown")
            dx = ship.dest_x - ship.source_x
            dy = ship.dest_y - ship.source_y
            distance = (dx**2 + dy**2)**0.5
            optimal_time = (distance / ship.speed * 3600) if ship.speed > 0 else 0
            extra_time = self.sim.current_time - optimal_time
            content_lines.append(f"{ship_label}:")
            content_lines.append(f"  Optimal Time: {optimal_time:.1f} s")
            content_lines.append(f"  Extra Time: {extra_time:.1f} s")
            content_lines.append("")
        # Encounter classification counts:
        if hasattr(self.sim, "count_headon"):
            content_lines.append("Encounter Classifications:")
            content_lines.append(f"  Head-on: {self.sim.count_headon}")
            content_lines.append(f"  Crossing: {self.sim.count_crossing}")
            content_lines.append(f"  Overtaking: {self.sim.count_overtaking}")
            content_lines.append("")
        # Collision avoidance insights:
        if hasattr(self.sim, "collisions_avoided") and self.sim.collisions_avoided:
            content_lines.append("Collision Avoidance Events:")
            for msg in self.sim.collisions_avoided:
                content_lines.append(f"  {msg}")
            content_lines.append("")
        
        # Render all content lines with vertical scrolling.
        y = 50 - self.scroll_offset  # Starting y position adjusted by scroll offset.
        for line in content_lines:
            text = self.font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, y))
            y += self.line_height
        
        # Draw the buttons anchored at the bottom.
        draw_button(screen, self.btn_back_stats, "Back", self.font)
        draw_button(screen, self.btn_main_menu, "Main Menu", self.font)
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
