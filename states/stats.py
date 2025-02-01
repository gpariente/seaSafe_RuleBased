# states/stats.py
import pygame
from config import BASE_RESOLUTIONS, BG_COLOR
from draw_utils import draw_button

class StatsState:
    def __init__(self, screen, sim_state, scenario_data):
        self.screen = screen
        self.sim_state = sim_state  # Store the full SimulationState instance.
        self.scenario_data = scenario_data  # Stored separately if needed.
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["stats"]
        self.next_state = None
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_back_stats.collidepoint(event.pos):
                    # Return the stored simulation state (with its finished run) 
                    self.next_state = self.sim_state
                elif self.btn_main_menu.collidepoint(event.pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
    
    def update(self, dt):
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        self.scale_x = current_w / base_w
        self.scale_y = current_h / base_h
        self.btn_back_stats = pygame.Rect(int(50 * self.scale_x), int(500 * self.scale_y),
                                          int(120 * self.scale_x), int(40 * self.scale_y))
        self.btn_main_menu = pygame.Rect(int(200 * self.scale_x), int(500 * self.scale_y),
                                         int(120 * self.scale_x), int(40 * self.scale_y))
    
    def render(self, screen):
        screen.fill(BG_COLOR)
        y_offset = 50
        lines = []
        lines.append(f"Total Simulation Time: {self.sim_state.sim.current_time:.1f} s")
        lines.append("")
        lines.append("Heading Adjustments: " + str(len(self.sim_state.sim.ui_log) if hasattr(self.sim_state.sim, "ui_log") else 0))
        lines.append("")
        lines.append("Classifications:")
        lines.append("  Head-on: 0")
        lines.append("  Crossing: 0")
        lines.append("  Overtaking: 0")
        for line in lines:
            text = self.font.render(line, True, (255, 255, 255))
            screen.blit(text, (50, y_offset))
            y_offset += text.get_height() + 10
        draw_button(screen, self.btn_back_stats, "Back", self.font)
        draw_button(screen, self.btn_main_menu, "Main Menu", self.font)
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
