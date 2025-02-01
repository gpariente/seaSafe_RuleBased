# states/manual_ship_setup.py
import pygame
from config import BASE_RESOLUTIONS, BG_COLOR, BG_SCROLL_SPEED
from ui_component import TextBox
from draw_utils import draw_button, draw_minimap, draw_scrolling_bg
import math

def create_ship_boxes(num, font):
    ship_boxes = []
    start_y = 150
    for i in range(num):
        row = []
        row.append(TextBox((80, start_y, 80, 30), font, "20"))
        row.append(TextBox((180, start_y, 100, 30), font, "0,0"))
        row.append(TextBox((300, start_y, 100, 30), font, "5,5"))
        row.append(TextBox((420, start_y, 80, 30), font, "300"))
        row.append(TextBox((520, start_y, 80, 30), font, "50"))
        ship_boxes.append(row)
        start_y += 60
    return ship_boxes

class ManualShipSetupState:
    def __init__(self, screen, scenario_data):
        self.screen = screen
        self.font = pygame.font.SysFont(None, 28)
        self.base_resolution = BASE_RESOLUTIONS["manual_ship_setup"]
        self.scenario_data = scenario_data
        self.ship_boxes = create_ship_boxes(scenario_data["num_ships"], self.font)
        self.next_state = None
        self.buttons = {
            "back": pygame.Rect(50, 600, 120, 40),
            "start": pygame.Rect(250, 600, 120, 40)
        }
        # For moving background:
        self.bg_img = None
        self.bg_scroll_x = 0.0
        self.last_dt = 0.0

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.scaled_buttons["back"].collidepoint(event.pos):
                    from states.manual_scenario import ManualScenarioState
                    self.next_state = ManualScenarioState(self.screen)
                elif self.scaled_buttons["start"].collidepoint(event.pos):
                    ships = []
                    for i, row in enumerate(self.ship_boxes):
                        speedBox, startBox, destBox, lenBox, widBox = row
                        speed = speedBox.get_float(20)
                        try:
                            sx, sy = map(float, startBox.get_str().split(','))
                        except:
                            sx, sy = 0.0, 0.0
                        try:
                            dx, dy = map(float, destBox.get_str().split(','))
                        except:
                            dx, dy = 5.0, 5.0
                        length_ = lenBox.get_float(300)
                        width_ = widBox.get_float(50)
                        heading = math.degrees(math.atan2(dy - sy, dx - sx)) if (dx,dy) != (sx,sy) else 0.0
                        ship_data = {
                            "name": f"Ship{i+1}",
                            "heading": heading,
                            "speed": speed,
                            "start_x": sx,
                            "start_y": sy,
                            "dest_x": dx,
                            "dest_y": dy,
                            "length_m": length_,
                            "width_m": width_
                        }
                        ships.append(ship_data)
                    self.scenario_data["ships"] = ships
                    from states.simulation_ui import SimulationState
                    self.next_state = SimulationState(self.screen, self.scenario_data)
            for row in self.ship_boxes:
                for tb in row:
                    tb.handle_event(event)
    
    def update(self, dt):
        self.last_dt = dt
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
        for row in self.ship_boxes:
            for tb in row:
                tb.update_rect(self.scale_x, self.scale_y)
        # Load background image if not loaded
        if self.bg_img is None:
            try:
                self.bg_img = pygame.image.load("./images/sea_bg.png").convert()
            except:
                self.bg_img = None
    
    def render(self, screen):
        # Draw moving background first
        if self.bg_img:
            self.bg_scroll_x = draw_scrolling_bg(screen, self.bg_img, self.bg_scroll_x, BG_SCROLL_SPEED, self.last_dt)
        else:
            screen.fill(BG_COLOR)
        header = self.font.render("Speed | Start(x,y) | Dest(x,y) | Length(m) | Width(m)", True, (255,255,255))
        screen.blit(header, (80 * self.scale_x, 90 * self.scale_y))
        y = 150
        for i, row in enumerate(self.ship_boxes):
            ship_label = self.font.render(f"Ship {i+1}", True, (255,255,255))
            screen.blit(ship_label, (10 * self.scale_x, y * self.scale_y + 10 * self.scale_y))
            for tb in row:
                tb.draw(screen)
            y += 60
        draw_button(screen, self.scaled_buttons["back"], "Back", self.font,color=(0,100,180))
        draw_button(screen, self.scaled_buttons["start"], "Start", self.font,color=(0,100,180))
        # Draw a minimap (dummy version)
        dummy_ships = []
        ship_colors = [(0,255,0), (255,255,0), (128,128,128), (0,0,0), (128,0,128)]
        for i, row in enumerate(self.ship_boxes):
            startBox = row[1]
            destBox = row[2]
            try:
                sx, sy = map(float, startBox.get_str().split(','))
            except:
                sx, sy = 0.0, 0.0
            try:
                dx, dy = map(float, destBox.get_str().split(','))
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
    
    def get_next_state(self):
        next_state = self.next_state
        self.next_state = None
        return next_state
