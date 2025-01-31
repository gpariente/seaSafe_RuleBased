# main.py
import pygame
import sys
import math
import json
import tkinter as tk
import tkinter.filedialog as fd

# Import collision logic from simulator.py, ship from ship.py
from simulator import Simulator
from ship import Ship

###############################################################################
# 1) States
###############################################################################
STATE_MAIN_MENU         = 1
STATE_AUTO_MODE         = 2
STATE_MANUAL_SCENARIO   = 3
STATE_MANUAL_SHIP_SETUP = 4
STATE_SIMULATION        = 5

###############################################################################
# 2) TextBox for UI
###############################################################################
class TextBox:
    def __init__(self, rect, font, initial_text=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.text = initial_text
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                pass
            else:
                self.text += event.unicode

    def draw(self, screen):
        color = (40, 200, 40) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))

    def get_str(self):
        return self.text.strip()

    def get_float(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default

    def get_int(self, default=0):
        try:
            return int(self.text)
        except ValueError:
            return default

###############################################################################
# 3) Helper Functions
###############################################################################
def draw_button(screen, rect, text, font, color=(0, 0, 200)):
    pygame.draw.rect(screen, color, rect, border_radius=5)
    label = font.render(text, True, (255, 255, 255))
    lx = rect.x + (rect.width - label.get_width()) / 2
    ly = rect.y + (rect.height - label.get_height()) / 2
    screen.blit(label, (lx, ly))

def parse_xy(s):
    s = s.replace(',', ' ')
    parts = s.split()
    if len(parts) == 2:
        try:
            x = float(parts[0])
            y = float(parts[1])
            return (x, y)
        except:
            pass
    return (0.0, 0.0)

def draw_scrolling_bg(screen, bg_img, scroll_x, scroll_speed, dt):
    w = bg_img.get_width()
    scroll_x += scroll_speed * dt
    scroll_x = scroll_x % w

    screen.blit(bg_img, (-scroll_x, 0))
    screen.blit(bg_img, (-scroll_x + w, 0))

    return scroll_x

def draw_ship_trail(screen, ship, nm_to_px, map_height, offset_x=0, offset_y=0):
    if len(ship.trail) < 2:
        return
    color = ship.color
    for i in range(1, len(ship.trail)):
        x1, y1 = ship.trail[i - 1]
        x2, y2 = ship.trail[i]
        sx1 = offset_x + x1 * nm_to_px
        sy1 = offset_y + map_height - (y1 * nm_to_px)
        sx2 = offset_x + x2 * nm_to_px
        sy2 = offset_y + map_height - (y2 * nm_to_px)
        pygame.draw.line(screen, color, (sx1, sy1), (sx2, sy2), 2)

def draw_ship_rect(screen, ship, nm_to_px, map_height, offset_x=0, offset_y=0):
    length_nm = ship.length_m / 1852.0
    width_nm  = ship.width_m  / 1852.0
    length_px = length_nm * nm_to_px
    width_px  = width_nm  * nm_to_px

    x_screen = offset_x + ship.x * nm_to_px
    y_screen = offset_y + map_height - (ship.y * nm_to_px)

    surf_l = max(1, int(length_px))
    surf_w = max(1, int(width_px))
    ship_surf = pygame.Surface((surf_l, surf_w), pygame.SRCALPHA)
    ship_surf.fill(ship.color)

    angle_for_pygame = ship.heading
    rotated = pygame.transform.rotate(ship_surf, angle_for_pygame)
    rect = rotated.get_rect()
    rect.center = (x_screen, y_screen)
    screen.blit(rotated, rect)

def draw_safety_circle(screen, ship, safe_distance_nm, nm_to_px, map_height, offset_x=0, offset_y=0):
    radius_px = int(safe_distance_nm * nm_to_px)
    center_x = int(offset_x + ship.x * nm_to_px)
    center_y = int(offset_y + map_height - (ship.y * nm_to_px))
    if radius_px > 0:
        pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), radius_px, 1)

        
def draw_y_axis_panel(screen, panel_rect, map_size, font):
    """
    Draws a vertical coordinate system (y-axis) in the provided panel.
    """
    pygame.draw.rect(screen, (220, 220, 220), panel_rect)  # Light grey background
    axis_x = panel_rect.x + 30
    axis_top = panel_rect.y + 10
    axis_bottom = panel_rect.y + panel_rect.height - 10
    pygame.draw.line(screen, (0, 0, 0), (axis_x, axis_top), (axis_x, axis_bottom), 2)
    num_ticks = 5
    for i in range(num_ticks):
        fraction = i / (num_ticks - 1)
        y_pos = axis_bottom - fraction * (axis_bottom - axis_top)
        pygame.draw.line(screen, (0, 0, 0), (axis_x, y_pos), (axis_x - 10, y_pos), 2)
        value = fraction * map_size
        label = font.render(f"{value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect()
        label_rect.right = axis_x - 12
        label_rect.centery = y_pos
        screen.blit(label, label_rect)

def draw_x_axis_panel(screen, panel_rect, map_size, font):
    """
    Draws a horizontal coordinate system (x-axis) in the provided panel.
    """
    pygame.draw.rect(screen, (220, 220, 220), panel_rect)
    axis_y = panel_rect.y + 20
    axis_left = panel_rect.x + 10
    axis_right = panel_rect.x + panel_rect.width - 10
    pygame.draw.line(screen, (0, 0, 0), (axis_left, axis_y), (axis_right, axis_y), 2)
    num_ticks = 5
    for i in range(num_ticks):
        fraction = i / (num_ticks - 1)
        x_pos = axis_left + fraction * (axis_right - axis_left)
        pygame.draw.line(screen, (0, 0, 0), (x_pos, axis_y), (x_pos, axis_y + 10), 2)
        value = fraction * map_size
        label = font.render(f"{value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect()
        label_rect.centerx = x_pos
        label_rect.top = axis_y + 12
        screen.blit(label, label_rect)
        
def draw_y_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    """
    Draws y-axis tick marks and labels in the left margin.
    margin_rect: a pygame.Rect representing the left margin area.
    map_size: map size in NM.
    tick_step: spacing between ticks in NM.
    """
    bg_color = (130, 180, 255)  # Same as the map background.
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Compute the y coordinate in the margin to match the map’s vertical scale.
        y = margin_rect.bottom - (tick_value / map_size) * margin_rect.height
        # Draw a small horizontal tick mark at the right edge of the margin.
        tick_start = (margin_rect.right - 10, y)
        tick_end = (margin_rect.right, y)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        # Render the label (aligned to the right of the margin).
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midright=(margin_rect.right - 12, y))
        screen.blit(label, label_rect)

def draw_x_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    """
    Draws x-axis tick marks and labels in the bottom margin.
    margin_rect: a pygame.Rect representing the bottom margin area.
    map_size: map size in NM.
    tick_step: spacing between ticks in NM.
    """
    bg_color = (130, 180, 255)  # Use the same background color as the map.
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Compute the x coordinate in the margin (matching the map’s horizontal scale).
        x = margin_rect.left + (tick_value / map_size) * margin_rect.width
        # Draw a small vertical tick mark at the top of the margin.
        tick_start = (x, margin_rect.top)
        tick_end = (x, margin_rect.top + 10)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        # Render the label (centered horizontally, just below the tick mark).
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midtop=(x, margin_rect.top + 12))
        screen.blit(label, label_rect)



def draw_grid(screen, map_rect, map_size, nm_to_px, tick_step=0.5, color=(200,200,200)):
    """
    Draws a grid overlay on the map area using a fixed tick step.
    For example, with tick_step=0.5 and map_size=6, grid lines are drawn at every 0.5 NM.
    """
    num_ticks = int(map_size / tick_step) + 1
    # Vertical grid lines.
    for i in range(num_ticks):
        x = map_rect.left + i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (x, map_rect.top), (x, map_rect.bottom), 1)
    # Horizontal grid lines.
    for i in range(num_ticks):
        y = map_rect.bottom - i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (map_rect.left, y), (map_rect.right, y), 1)

def draw_x_axis_labels_on_map(screen, map_rect, map_size, font, tick_step=0.5):
    """
    Draws x-axis labels (tick values) directly on the bottom border of the map.
    The ticks are drawn at every tick_step (e.g., every 0.5 NM) so that the left and right 
    boundaries of the map show the correct values.
    """
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Calculate x coordinate along the bottom border.
        x = map_rect.left + (tick_value / map_size) * map_rect.width
        # Inset the label a few pixels inside the map.
        y = map_rect.bottom - 5
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midbottom=(x, y))
        screen.blit(label, label_rect)

def draw_y_axis_labels_on_map(screen, map_rect, map_size, font, tick_step=0.5):
    """
    Draws y-axis labels (tick values) directly on the left border of the map.
    The ticks are drawn at every tick_step (e.g., every 0.5 NM) so that the bottom and top 
    boundaries of the map show the correct values.
    """
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Calculate y coordinate (with 0 at the bottom).
        y = map_rect.bottom - (tick_value / map_size) * map_rect.height
        # Inset the label a few pixels inside the map.
        x = map_rect.left + 5
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midleft=(x, y))
        screen.blit(label, label_rect)



def draw_star(screen, center, radius, color):
    """
    Draws a 5-pointed star at the given center with the specified radius and color.
    """
    import math  # already imported in your file
    points = []
    inner_radius = radius * 0.5
    for i in range(10):
        angle = math.radians(i * 36)  # 36° between points
        r = radius if i % 2 == 0 else inner_radius
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(screen, color, points)


###############################################################################
# 5) Main Program
###############################################################################
def main():
    pygame.init()

    # We'll make the simulation screen 800 wide x 840 tall:
    # 800x800 for the map, + 40 px at the bottom for buttons
    # But for menu states, we still do 800x600
    screen_width, screen_height = 800, 600
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("SeaSafe Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    # Load assets
    try:
        sea_bg = pygame.image.load("./images/sea_bg.png").convert()
    except:
        sea_bg = pygame.Surface((800, 600))
        sea_bg.fill((0, 100, 200))

    try:
        logo_img = pygame.image.load("./images/logo.png").convert_alpha()
    except:
        logo_img = pygame.Surface((200, 100), pygame.SRCALPHA)
        pygame.draw.rect(logo_img, (255, 255, 255, 180), logo_img.get_rect())

    scale_factor = 2
    new_logo_width = int(logo_img.get_width() * scale_factor)
    new_logo_height = int(logo_img.get_height() * scale_factor)
    logo_img = pygame.transform.scale(logo_img, (new_logo_width, new_logo_height))
    logo_x = (800 - new_logo_width) // 2
    logo_y = 30

    sea_scroll_x = 0.0
    sea_scroll_speed = 30.0

    current_state = STATE_MAIN_MENU
    running = True

    scenario_data = {
        "map_size": 6.0,
        "safe_distance": 0.2,
        "heading_range": 40.0,
        "heading_step": 1.0,
        "time_step": 30.0,
        "ships": [],
        "num_ships": 1
    }

    automatic_loaded_ok = False
    sim = None
    ships = []
    ship_roles = {}
    nm_to_px = 100.0

    ship_colors = [
        (0, 255, 0),
        (255, 255, 0),
        (128, 128, 128),
        (0, 0, 0),
        (128, 0, 128)
    ]

    paused = False
    warning_msg_auto = ""

    def load_scenario_from_json():
        root = tk.Tk()
        root.withdraw()
        file_path = fd.askopenfilename(filetypes=[("JSON Files", "*.json")])
        root.destroy()
        if file_path:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                scenario_data["map_size"]      = data.get("map_size", 6.0)
                scenario_data["safe_distance"] = data.get("safe_distance", 0.2)
                scenario_data["heading_range"] = data.get("heading_range", 40)
                scenario_data["heading_step"]  = data.get("heading_step", 1)
                scenario_data["time_step"]     = data.get("time_step", 30)
                scenario_data["ships"]         = data.get("ships", [])
                return True
            except:
                return False
        return False

    font_small = pygame.font.SysFont(None, 24)

    box_map_size    = TextBox((300, 100, 120, 30), font, "6")
    box_safe_dist   = TextBox((300, 150, 120, 30), font, "0.2")
    box_search_rng  = TextBox((300, 200, 120, 30), font, "40")
    box_search_step = TextBox((300, 250, 120, 30), font, "1")
    box_time_step   = TextBox((300, 300, 120, 30), font, "30")
    box_num_ships   = TextBox((300, 350, 120, 30), font, "1")

    ship_boxes = []
    def create_ship_boxes(num):
        new_list = []
        start_y = 150
        for i in range(num):
            row = []
            row.append(TextBox((80, start_y, 80, 30), font, "20"))
            row.append(TextBox((180, start_y, 100, 30), font, "0,0"))
            row.append(TextBox((300, start_y, 100, 30), font, "5,5"))
            row.append(TextBox((420, start_y, 80, 30), font, "300"))
            row.append(TextBox((520, start_y, 80, 30), font, "50"))
            new_list.append(row)
            start_y += 60
        return new_list

    manual_setup_screen_set = False

    # We'll track scenario_finished and show replay/back buttons
    scenario_finished = False

    while running:
        dt = clock.tick(30) / 1000.0

        if current_state in (STATE_MAIN_MENU, STATE_AUTO_MODE, STATE_MANUAL_SCENARIO):
            sea_scroll_x = draw_scrolling_bg(screen, sea_bg, sea_scroll_x, sea_scroll_speed, dt)

        if current_state == STATE_MAIN_MENU:
            if screen.get_size() != (800,600):
                screen = pygame.display.set_mode((800,600))
                pygame.display.set_caption("SeaSafe Simulator")
            screen.blit(logo_img, (logo_x, logo_y))
            btn_manual = pygame.Rect((800 - 200)//2, 250, 200, 50)
            btn_auto   = pygame.Rect((800 - 200)//2, 340, 200, 50)
            btn_exit   = pygame.Rect((800 - 200)//2, 430, 200, 50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_manual.collidepoint(event.pos):
                        current_state = STATE_MANUAL_SCENARIO
                    elif btn_auto.collidepoint(event.pos):
                        current_state = STATE_AUTO_MODE
                    elif btn_exit.collidepoint(event.pos):
                        running = False

            draw_button(screen, btn_manual, "Manual Mode", font, color=(0, 100, 180))
            draw_button(screen, btn_auto,   "Automatic Mode", font, color=(0, 100, 180))
            draw_button(screen, btn_exit,   "Exit",           font, color=(0, 100, 180))
            pygame.display.flip()

        elif current_state == STATE_AUTO_MODE:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            btn_back  = pygame.Rect(50, 500, 100, 40)
            btn_load  = pygame.Rect(300, 200, 200, 50)
            btn_start = pygame.Rect(300, 300, 200, 50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_load.collidepoint(event.pos):
                        ok = load_scenario_from_json()
                        if not ok:
                            warning_msg_auto = "Error: Invalid or non-JSON file!"
                            automatic_loaded_ok = False
                        else:
                            # if loaded, check if ships exist
                            if len(scenario_data["ships"]) == 0:
                                warning_msg_auto = "No ships found in scenario!"
                                automatic_loaded_ok = False
                            else:
                                warning_msg_auto = "JSON loaded successfully."
                                automatic_loaded_ok = True
                    elif btn_start.collidepoint(event.pos):
                        if automatic_loaded_ok and len(scenario_data["ships"]) > 0:
                            current_state = STATE_SIMULATION
                        else:
                            warning_msg_auto = "No valid JSON or no ships loaded!"

            draw_button(screen, btn_back,  "Back",  font)
            draw_button(screen, btn_load,  "Load JSON", font)
            draw_button(screen, btn_start, "Start", font)

            if warning_msg_auto:
                msg_surf = font.render(warning_msg_auto, True, (255, 0, 0))
                screen.blit(msg_surf, (200, 400))

            pygame.display.flip()

        elif current_state == STATE_MANUAL_SCENARIO:
            overlay = pygame.Surface((800, 600), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            btn_back = pygame.Rect(50, 500, 100, 40)
            btn_next = pygame.Rect(600, 500, 100, 40)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_next.collidepoint(event.pos):
                        scenario_data["map_size"]      = box_map_size.get_float(6.0)
                        scenario_data["safe_distance"] = box_safe_dist.get_float(0.2)
                        scenario_data["heading_range"] = box_search_rng.get_float(40)
                        scenario_data["heading_step"]  = box_search_step.get_float(1)
                        scenario_data["time_step"]     = box_time_step.get_float(30)
                        scenario_data["num_ships"]     = box_num_ships.get_int(1)

                        ship_boxes = create_ship_boxes(scenario_data["num_ships"])
                        scenario_data["ship_boxes"] = ship_boxes
                        current_state = STATE_MANUAL_SHIP_SETUP

                box_map_size.handle_event(event)
                box_safe_dist.handle_event(event)
                box_search_rng.handle_event(event)
                box_search_step.handle_event(event)
                box_time_step.handle_event(event)
                box_num_ships.handle_event(event)

            label = font.render("Map Size:", True, (255, 255, 255))
            screen.blit(label, (box_map_size.rect.x - label.get_width() - 5, box_map_size.rect.y))
            label = font.render("SafeDist:", True, (255, 255, 255))
            screen.blit(label, (box_safe_dist.rect.x - label.get_width() - 5, box_safe_dist.rect.y))
            label = font.render("SearchRange:", True, (255, 255, 255))
            screen.blit(label, (box_search_rng.rect.x - label.get_width() - 5, box_search_rng.rect.y))
            label = font.render("SearchStep:", True, (255, 255, 255))
            screen.blit(label, (box_search_step.rect.x - label.get_width() - 5, box_search_step.rect.y))
            label = font.render("TimeStep:", True, (255, 255, 255))
            screen.blit(label, (box_time_step.rect.x - label.get_width() - 5, box_time_step.rect.y))
            label = font.render("#Ships:", True, (255, 255, 255))
            screen.blit(label, (box_num_ships.rect.x - label.get_width() - 5, box_num_ships.rect.y))

            box_map_size.draw(screen)
            box_safe_dist.draw(screen)
            box_search_rng.draw(screen)
            box_search_step.draw(screen)
            box_time_step.draw(screen)
            box_num_ships.draw(screen)

            draw_button(screen, btn_back, "Back", font)
            draw_button(screen, btn_next, "Next", font)
            pygame.display.flip()

        elif current_state == STATE_MANUAL_SHIP_SETUP:
            if not manual_setup_screen_set:
                screen = pygame.display.set_mode((900, 700))
                pygame.display.set_caption("Ship Setup")
                manual_setup_screen_set = True

            dt_ms = clock.tick(30)
            dt_manual = dt_ms / 1000.0
            sea_scroll_x = draw_scrolling_bg(screen, sea_bg, sea_scroll_x, sea_scroll_speed, dt_manual)

            overlay = pygame.Surface((900, 700), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 100))
            screen.blit(overlay, (0, 0))

            btn_back  = pygame.Rect(50, 600, 120, 40)
            btn_start = pygame.Rect(250, 600, 120, 40)

            local_ship_boxes = scenario_data.get("ship_boxes", [])

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        screen = pygame.display.set_mode((800, 600))
                        pygame.display.set_caption("SeaSafe Simulator")
                        manual_setup_screen_set = False
                        current_state = STATE_MANUAL_SCENARIO
                    elif btn_start.collidepoint(event.pos):
                        scenario_data["ships"] = []
                        for i, row in enumerate(local_ship_boxes):
                            speedBox, startBox, destBox, lenBox, widBox = row
                            speed = speedBox.get_float(20)
                            sx, sy = parse_xy(startBox.get_str())
                            dx_, dy_ = parse_xy(destBox.get_str())
                            length_ = lenBox.get_float(300)
                            width_  = widBox.get_float(50)

                            heading = 0.0
                            dxval = dx_ - sx
                            dyval = dy_ - sy
                            if abs(dxval) > 1e-7 or abs(dyval) > 1e-7:
                                heading = math.degrees(math.atan2(dyval, dxval))

                            sname = f"Ship{i+1}"
                            scenario_data["ships"].append({
                                "name": sname,
                                "heading": heading,
                                "speed": speed,
                                "start_x": sx,
                                "start_y": sy,
                                "dest_x": dx_,
                                "dest_y": dy_,
                                "length_m": length_,
                                "width_m": width_
                            })

                        screen = pygame.display.set_mode((800, 600))
                        pygame.display.set_caption("SeaSafe Simulator")
                        manual_setup_screen_set = False
                        current_state = STATE_SIMULATION

                for row in local_ship_boxes:
                    for tb in row:
                        tb.handle_event(event)

            header_surf = font.render("Speed | Start(x,y) | Dest(x,y) | Length(m) | Width(m)", True, (255, 255, 255))
            screen.blit(header_surf, (80, 90))

            y = 150
            for i, row in enumerate(local_ship_boxes):
                label_ship = font.render(f"Ship {i+1} ", True, (255, 255, 255))
                screen.blit(label_ship, (10, y + 10))
                for tb in row:
                    tb.draw(screen)
                y += 60

            draw_button(screen, btn_back,  "Back",  font)
            draw_button(screen, btn_start, "Start", font)
            pygame.display.flip()

        elif current_state == STATE_SIMULATION:
            # Layout configuration:
            left_label_margin = 60    # Left margin for y-axis labels.
            top_margin = 20
            map_width = 800
            map_height = 800
            bottom_margin = 60        # Bottom margin for x-axis labels.
            ui_panel_height = 40      # UI panel for buttons below the x-axis margin.
            right_margin = 20
            total_width = left_label_margin + map_width + right_margin
            total_height = top_margin + map_height + bottom_margin + ui_panel_height

            # Always set the display mode and caption (this is safe to call each iteration)
            screen = pygame.display.set_mode((total_width, total_height))
            pygame.display.set_caption("Collision Avoidance - Simulation")
            
            # Fill the entire background with the sea background color
            screen.fill((130, 180, 255))

            # Define rectangles for each area.
            map_rect = pygame.Rect(left_label_margin, top_margin, map_width, map_height)
            y_axis_margin_rect = pygame.Rect(0, top_margin, left_label_margin, map_height)
            x_axis_margin_rect = pygame.Rect(left_label_margin, top_margin + map_height, map_width, bottom_margin)
            ui_panel_rect = pygame.Rect(left_label_margin, top_margin + map_height + bottom_margin, map_width, ui_panel_height)

            # Define UI buttons (positioned within the UI panel).
            btn_back_sim   = pygame.Rect(left_label_margin + 10, ui_panel_rect.top + 5, 100, 35)
            btn_replay_sim = pygame.Rect(left_label_margin + 120, ui_panel_rect.top + 5, 100, 35)

            # -- Process events --
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back_sim.collidepoint(event.pos):
                        # Back: Return to the previous screen.
                        current_state = STATE_MAIN_MENU
                        sim = None
                        paused = False
                        scenario_finished = False
                    elif btn_replay_sim.collidepoint(event.pos):
                        # Replay: Restart the simulation.
                        sim = None
                        paused = False
                        scenario_finished = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused
                        
            if current_state != STATE_SIMULATION:
                continue

            # -- Reinitialize simulation if needed --
            # (This is placed after event processing so that if Replay was pressed,
            #  we immediately reinitialize the simulation.)
            if sim is None and current_state == STATE_SIMULATION:
                loaded_ships = []
                for i, sdata in enumerate(scenario_data["ships"]):
                    sname   = sdata.get("name", f"Ship{i+1}")
                    heading = sdata.get("heading", 0.0)
                    speed   = sdata.get("speed", 20.0)
                    sx      = sdata.get("start_x", 0.0)
                    sy      = sdata.get("start_y", 0.0)
                    dx_     = sdata.get("dest_x", 5.0)
                    dy_     = sdata.get("dest_y", 5.0)
                    length_ = sdata.get("length_m", 300)
                    width_  = sdata.get("width_m", 50)
                    ship_obj = Ship(sname, sx, sy, heading, speed, dx_, dy_, length_, width_)
                    ship_obj.color = ship_colors[i % len(ship_colors)]
                    ship_obj.trail = []
                    loaded_ships.append(ship_obj)
                sim = Simulator(
                    ships=loaded_ships,
                    time_step=scenario_data["time_step"],
                    safe_distance=scenario_data["safe_distance"],
                    heading_search_range=scenario_data["heading_range"],
                    heading_search_step=scenario_data["heading_step"]
                )
                ships = sim.ships
                ship_roles = {sh.name: "" for sh in ships}
                nm_to_px = map_width / scenario_data["map_size"]
                scenario_finished = False
                paused = False

            # -- Simulation update --
            if not scenario_finished and sim is not None and not paused:
                sim.step(debug=False)
                for sh in ships:
                    sh.trail.append((sh.x, sh.y))
                if sim.all_ships_arrived():
                    scenario_finished = True

            # -- Drawing --
            # Draw the map background and grid.
            pygame.draw.rect(screen, (130, 180, 255), map_rect)
            draw_grid(screen, map_rect, scenario_data["map_size"], nm_to_px, tick_step=0.5)

            # Draw ship trails, safety circles, and ships.
            for s in ships:
                draw_ship_trail(screen, s, nm_to_px, map_height, offset_x=left_label_margin, offset_y=top_margin)
                draw_safety_circle(screen, s, sim.safe_distance, nm_to_px, map_height, offset_x=left_label_margin, offset_y=top_margin)
                draw_ship_rect(screen, s, nm_to_px, map_height, offset_x=left_label_margin, offset_y=top_margin)
            # Draw destination markers (colored stars).
            for s in ships:
                dest_x_screen = left_label_margin + s.dest_x * nm_to_px
                dest_y_screen = top_margin + map_height - (s.dest_y * nm_to_px)
                draw_star(screen, (dest_x_screen, dest_y_screen), 8, s.color)

            # Draw informational labels.
            time_label = font.render(f"Current Time Step: {sim.current_time}s", True, (0, 0, 0))
            screen.blit(time_label, (left_label_margin + 10, top_margin + 10))
            space_label = font.render("Press SPACE to Pause/Resume", True, (200, 0, 0))
            screen.blit(space_label, (left_label_margin + 10, top_margin + 30))
            if paused:
                pause_text = font.render("PAUSED", True, (255, 0, 0))
                screen.blit(pause_text, (left_label_margin + 10, top_margin + 50))
            if scenario_finished:
                finish_text = font.render("Scenario finished - all ships reached destinations!", True, (0,150,0))
                fx = left_label_margin + (map_width - finish_text.get_width()) // 2
                fy = top_margin + map_height // 2 - finish_text.get_height() // 2
                screen.blit(finish_text, (fx, fy))

            # Draw the y-axis and x-axis labels in their dedicated margins.
            draw_y_axis_labels_in_margin(screen, y_axis_margin_rect, scenario_data["map_size"], font, tick_step=0.5)
            draw_x_axis_labels_in_margin(screen, x_axis_margin_rect, scenario_data["map_size"], font, tick_step=0.5)
            
            # Draw the missing horizontal grid line along the bottom edge of the map.
            pygame.draw.line(
                screen,
                (200, 200, 200),
                (left_label_margin, top_margin + map_height),
                (left_label_margin + map_width, top_margin + map_height),
                1
            )
            
            # Draw the UI panel and buttons.
            pygame.draw.rect(screen, (60,60,60), ui_panel_rect)
            draw_button(screen, btn_back_sim, "Back", font)
            draw_button(screen, btn_replay_sim, "Replay", font)

            pygame.display.flip()
            clock.tick(3)


        else:
            running = False

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
