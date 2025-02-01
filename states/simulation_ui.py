# states/simulation_ui.py
import pygame
from config import BASE_RESOLUTIONS, LEFT_MARGIN, TOP_MARGIN, BOTTOM_MARGIN, UI_PANEL_HEIGHT, BG_COLOR
from draw_utils import (draw_grid, draw_ship_trail, draw_safety_circle, draw_ship_rect,
                        draw_star, draw_y_axis_labels_in_margin, draw_x_axis_labels_in_margin,
                        draw_dashed_line, draw_button)
from simulator import Simulator
from ship import Ship

class SimulationState:
    def __init__(self, screen, scenario_data=None):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["simulation"]
        self.next_state = None
        self.scenario_data = scenario_data if scenario_data is not None else {}
        self.sim = None
        self.paused = False
        self.scenario_finished = False
        self.compare_mode = False
        self.sea_scroll_x = 0.0
        self.sea_scroll_speed = 30.0
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.btn_back_sim.collidepoint(event.pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
                    self.sim = None
                    self.paused = False
                    self.scenario_finished = False
                    self.compare_mode = False
                elif self.btn_replay_sim.collidepoint(event.pos):
                    self.sim = None
                    self.paused = False
                    self.scenario_finished = False
                    self.compare_mode = False
                elif self.btn_compare.collidepoint(event.pos) and self.scenario_finished:
                    self.compare_mode = not self.compare_mode
                elif self.btn_next.collidepoint(event.pos) and self.scenario_finished:
                    from states.stats import StatsState
                    self.next_state = StatsState(self.screen, self, self.scenario_data)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
    
    def update(self, dt):
        current_w, current_h = self.screen.get_size()
        base_w, base_h = self.base_resolution
        self.scale = min(current_w / base_w, current_h / base_h)
        self.sim_area_w = int(base_w * self.scale)
        self.sim_area_h = int(base_h * self.scale)
        self.offset_sim_x = (current_w - self.sim_area_w) // 2
        self.offset_sim_y = (current_h - self.sim_area_h) // 2

        self.left_margin = int(LEFT_MARGIN * self.scale)
        self.top_margin = int(TOP_MARGIN * self.scale)
        self.map_width = int(800 * self.scale)
        self.map_height = int(800 * self.scale)
        self.bottom_margin = int(BOTTOM_MARGIN * self.scale)
        self.ui_panel_height = int(UI_PANEL_HEIGHT * self.scale)
        self.ui_panel_y = self.offset_sim_y + self.top_margin + self.map_height + self.bottom_margin

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
    
        if self.sim is None:
            ships = []
            ship_datas = self.scenario_data.get("ships")
            if not ship_datas:
                ship_datas = [{
                    "name": "Ship1", "heading": 0.0, "speed": 20.0,
                    "start_x": 0.0, "start_y": 0.0, "dest_x": 5.0, "dest_y": 5.0,
                    "length_m": 300, "width_m": 50
                }]
            ship_colors = [(0,255,0), (255,255,0), (128,128,128), (0,0,0), (128,0,128)]
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
                ship.color = ship_colors[i % len(ship_colors)]
                ship.trail = []
                ship.source_x = sx
                ship.source_y = sy
                ships.append(ship)
            from simulator import Simulator
            self.sim = Simulator(
                ships=ships,
                time_step=self.scenario_data.get("time_step", 30),
                safe_distance=self.scenario_data.get("safe_distance", 0.2),
                heading_search_range=self.scenario_data.get("heading_range", 40),
                heading_search_step=self.scenario_data.get("heading_step", 1)
            )
            self.scenario_data.setdefault("map_size", 6.0)
            self.scenario_finished = False
            self.paused = False
            self.compare_mode = False
    
        if not self.scenario_finished and not self.paused:
            self.sim.step(debug=False)
            for sh in self.sim.ships:
                sh.trail.append((sh.x, sh.y))
            if self.sim.all_ships_arrived():
                self.scenario_finished = True
    
    def render(self, screen):
        screen.fill(BG_COLOR)
        simulation_area_rect = pygame.Rect(self.offset_sim_x, self.offset_sim_y, self.sim_area_w, self.sim_area_h)
        pygame.draw.rect(screen, BG_COLOR, simulation_area_rect)
        map_rect = pygame.Rect(self.offset_sim_x + self.left_margin,
                               self.offset_sim_y + self.top_margin,
                               self.map_width, self.map_height)
        sim_font = pygame.font.SysFont(None, int(28 * self.scale))
        nm_to_px = self.map_width / self.scenario_data.get("map_size", 6.0)
        from draw_utils import draw_grid, draw_ship_trail, draw_safety_circle, draw_ship_rect, draw_star
        draw_grid(screen, map_rect, self.scenario_data.get("map_size", 6.0), nm_to_px, tick_step=0.5)
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
        for s in self.sim.ships:
            dest_x_screen = self.offset_sim_x + self.left_margin + int(s.dest_x * nm_to_px)
            dest_y_screen = self.offset_sim_y + self.top_margin + self.map_height - int(s.dest_y * nm_to_px)
            draw_star(screen, (dest_x_screen, dest_y_screen), int(8 * self.scale), s.color)
        
        time_label = sim_font.render(f"Current Time Step: {self.sim.current_time}s", True, (0,0,0))
        screen.blit(time_label, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                 self.offset_sim_y + self.top_margin + int(10 * self.scale)))
        space_label = sim_font.render("Press SPACE to Pause/Resume", True, (200,0,0))
        screen.blit(space_label, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                  self.offset_sim_y + self.top_margin + int(30 * self.scale)))
        if self.paused:
            pause_text = sim_font.render("PAUSED", True, (255,0,0))
            screen.blit(pause_text, (self.offset_sim_x + self.left_margin + int(10 * self.scale),
                                     self.offset_sim_y + self.top_margin + int(50 * self.scale)))
        from draw_utils import draw_y_axis_labels_in_margin, draw_x_axis_labels_in_margin
        draw_y_axis_labels_in_margin(screen,
            pygame.Rect(self.offset_sim_x, self.offset_sim_y + self.top_margin, self.left_margin, self.map_height),
            self.scenario_data.get("map_size", 6.0), sim_font, tick_step=0.5)
        draw_x_axis_labels_in_margin(screen,
            pygame.Rect(self.offset_sim_x + self.left_margin, self.offset_sim_y + self.top_margin + self.map_height, self.map_width, BOTTOM_MARGIN),
            self.scenario_data.get("map_size", 6.0), sim_font, tick_step=0.5)
        pygame.draw.line(screen, (200,200,200),
                         (self.offset_sim_x + self.left_margin, self.offset_sim_y + self.top_margin + self.map_height),
                         (self.offset_sim_x + self.left_margin + self.map_width, self.offset_sim_y + self.top_margin + self.map_height),
                         1)
        ui_panel_rect = pygame.Rect(self.offset_sim_x + self.left_margin, self.ui_panel_y, self.map_width, self.ui_panel_height)
        pygame.draw.rect(screen, (60,60,60), ui_panel_rect)
        draw_button(screen, self.btn_back_sim, "Back", sim_font)
        draw_button(screen, self.btn_replay_sim, "Replay", sim_font)
        if self.scenario_finished:
            if self.compare_mode:
                from draw_utils import draw_dashed_line
                for s in self.sim.ships:
                    start_pos = (self.offset_sim_x + self.left_margin + int(s.source_x * nm_to_px),
                                 self.offset_sim_y + self.top_margin + self.map_height - int(s.source_y * nm_to_px))
                    end_pos = (self.offset_sim_x + self.left_margin + int(s.dest_x * nm_to_px),
                               self.offset_sim_y + self.top_margin + self.map_height - int(s.dest_y * nm_to_px))
                    draw_dashed_line(screen, s.color, start_pos, end_pos, dash_length=int(5*self.scale), space_length=int(10*self.scale))
            else:
                finish_text = sim_font.render("Scenario finished - all ships reached destinations!", True, (0,150,0))
                fx = self.offset_sim_x + self.left_margin + (self.map_width - finish_text.get_width()) // 2
                fy = self.offset_sim_y + self.top_margin + self.map_height//2 - finish_text.get_height()//2
                screen.blit(finish_text, (fx,fy))
            draw_button(screen, self.btn_compare, "Compare", sim_font)
            draw_button(screen, self.btn_next, "Next", sim_font)
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
