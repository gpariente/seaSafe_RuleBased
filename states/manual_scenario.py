# states/manual_scenario.py
import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from ui_component import TextBox
from draw_utils import draw_button, draw_scrolling_bg
from states.manual_ship_setup import ManualShipSetupState

class ManualScenarioState:
    def __init__(self, screen):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["manual_scenario"]
        self.next_state = None
        # Create text boxes for scenario parameters
        self.box_map_size = TextBox((300, 100, 120, 30), self.font, "6")
        self.box_safe_dist = TextBox((300, 150, 120, 30), self.font, "0.2")
        self.box_search_rng = TextBox((300, 200, 120, 30), self.font, "40")
        self.box_search_step = TextBox((300, 250, 120, 30), self.font, "1")
        self.box_time_step = TextBox((300, 300, 120, 30), self.font, "30")
        self.box_num_ships = TextBox((300, 350, 120, 30), self.font, "1")
        self.text_boxes = [self.box_map_size, self.box_safe_dist, self.box_search_rng,
                           self.box_search_step, self.box_time_step, self.box_num_ships]
        self.buttons = {
            "back": pygame.Rect(50, 500, 100, 40),
            "next": pygame.Rect(600, 500, 100, 40)
        }
        # For moving background
        self.bg_img = None
        self.bg_scroll_x = 0.0
        self.last_dt = 0.0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.scaled_buttons["back"].collidepoint(event.pos):
                    from states.main_menu import MainMenuState
                    self.next_state = MainMenuState(self.screen)
                elif self.scaled_buttons["next"].collidepoint(event.pos):
                    scenario_data = {
                        "map_size": self.box_map_size.get_float(6.0),
                        "safe_distance": self.box_safe_dist.get_float(0.2),
                        "heading_range": self.box_search_rng.get_float(40),
                        "heading_step": self.box_search_step.get_float(1),
                        "time_step": self.box_time_step.get_float(30),
                        "num_ships": self.box_num_ships.get_int(1)
                    }
                    self.scenario_data = scenario_data
                    self.next_state = ManualShipSetupState(self.screen, scenario_data)
            for tb in self.text_boxes:
                tb.handle_event(event)
    
    def update(self, dt):
        self.last_dt = dt  # Save dt for use in render() for background scrolling
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
        for tb in self.text_boxes:
            tb.update_rect(self.scale_x, self.scale_y)
        # Load background image if not loaded
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None
    
    def render(self, screen):
        # Draw scrolling background
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, self.last_dt)
        else:
            screen.fill(BG_COLOR)
        # Draw the UI elements on top
        labels = ["Map Size:", "Safety Zone:", "Heading Range:", "Heading Step:", "Time Step:", "#Ships:"]
        for tb, label_text in zip(self.text_boxes, labels):
            label = self.font.render(label_text, True, (255,255,255))
            screen.blit(label, (tb.rect.x - label.get_width() - 5, tb.rect.y))
            tb.draw(screen)
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font,color=(0,100,180))
        draw_button(screen, self.scaled_buttons["next"], "Next", self.font,color=(0,100,180))
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
