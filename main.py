# main.py
import pygame
import sys
import math
import json
import tkinter as tk
import tkinter.filedialog as fd
import numpy as np

# Import collision logic from simulator.py, ship from ship.py
from simulator import Simulator
from ship import Ship
from colreg import *

###############################################################################
# 1) States
###############################################################################
STATE_MAIN_MENU         = 1
STATE_AUTO_MODE         = 2
STATE_MANUAL_SCENARIO   = 3
STATE_MANUAL_SHIP_SETUP = 4
STATE_SIMULATION        = 5
STATE_STATS             = 6

# Base resolutions for each state (used for scaling)
BASE_RESOLUTIONS = {
    STATE_MAIN_MENU:         (800, 600),
    STATE_AUTO_MODE:         (800, 600),
    STATE_MANUAL_SCENARIO:   (800, 600),
    STATE_MANUAL_SHIP_SETUP: (900, 700),
    # For simulation: left_margin (60) + map_width (800) + right_margin (20) = 880;
    # top_margin (20) + map_height (800) + bottom_margin (60) + ui_panel (40) = 920.
    STATE_SIMULATION:        (880, 920),
    STATE_STATS:             (800, 840)
}

def get_scale_factors(state, current_size):
    base_w, base_h = BASE_RESOLUTIONS[state]
    current_w, current_h = current_size
    return current_w / base_w, current_h / base_h

###############################################################################
# 2) TextBox for UI (extended for dynamic resizing)
###############################################################################
class TextBox:
    def __init__(self, rect, font, initial_text=""):
        # Save the original rectangle as the "base" rectangle.
        self.base_rect = pygame.Rect(rect)
        self.rect = self.base_rect.copy()
        self.font = font
        self.text = initial_text
        self.active = False

    def update_rect(self, scale_x, scale_y):
        self.rect = pygame.Rect(
            int(self.base_rect.x * scale_x),
            int(self.base_rect.y * scale_y),
            int(self.base_rect.width * scale_x),
            int(self.base_rect.height * scale_y)
        )

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
# 3) Helper Functions (unchanged)
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
    width_px  = width_nm * nm_to_px
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

def draw_y_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    bg_color = (130, 180, 255)
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        y = margin_rect.bottom - (tick_value / map_size) * margin_rect.height
        tick_start = (margin_rect.right - 10, y)
        tick_end = (margin_rect.right, y)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midright=(margin_rect.right - 12, y))
        screen.blit(label, label_rect)

def draw_x_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    bg_color = (130, 180, 255)
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        x = margin_rect.left + (tick_value / map_size) * margin_rect.width
        tick_start = (x, margin_rect.top)
        tick_end = (x, margin_rect.top + 10)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midtop=(x, margin_rect.top + 12))
        screen.blit(label, label_rect)

def draw_grid(screen, map_rect, map_size, nm_to_px, tick_step=0.5, color=(200,200,200)):
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        x = map_rect.left + i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (x, map_rect.top), (x, map_rect.bottom), 1)
    for i in range(num_ticks):
        y = map_rect.bottom - i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (map_rect.left, y), (map_rect.right, y), 1)

def draw_star(screen, center, radius, color):
    points = []
    inner_radius = radius * 0.5
    for i in range(10):
        angle = math.radians(i * 36)
        r = radius if i % 2 == 0 else inner_radius
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(screen, color, points)

def draw_minimap(screen, ships, map_size, pos, size):
    minimap_rect = pygame.Rect(pos[0], pos[1], size, size)
    pygame.draw.rect(screen, (200, 200, 200), minimap_rect)
    pygame.draw.rect(screen, (0, 0, 0), minimap_rect, 2)
    scale = size / map_size
    for s in ships:
        src_x = pos[0] + s.x * scale
        src_y = pos[1] + size - s.y * scale
        pygame.draw.circle(screen, s.color, (int(src_x), int(src_y)), 3)
        dest_x = pos[0] + s.dest_x * scale
        dest_y = pos[1] + size - s.dest_y * scale
        draw_star(screen, (int(dest_x), int(dest_y)), 5, s.color)
    for i in range(int(map_size)+1):
        x = pos[0] + i * scale
        pygame.draw.line(screen, (100, 100, 100), (x, pos[1]), (x, pos[1]+size), 1)
        y = pos[1] + size - i * scale
        pygame.draw.line(screen, (100, 100, 100), (pos[0], y), (pos[0]+size, y), 1)

def draw_dashed_line(screen, color, start_pos, end_pos, dash_length=5, space_length=3):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dx = x2 - x1
    dy = y2 - y1
    distance = math.hypot(dx, dy)
    if distance == 0:
        return
    dash_count = int(distance // (dash_length + space_length))
    dash_dx = dx / distance * dash_length
    dash_dy = dy / distance * dash_length
    space_dx = dx / distance * space_length
    space_dy = dy / distance * space_length
    current_pos = start_pos
    for i in range(dash_count):
        next_pos = (current_pos[0] + dash_dx, current_pos[1] + dash_dy)
        pygame.draw.line(screen, color, current_pos, next_pos, 2)
        current_pos = (next_pos[0] + space_dx, next_pos[1] + space_dy)
    pygame.draw.line(screen, color, current_pos, end_pos, 2)

def draw_stats_screen(screen, sim, ships, font):
    screen.fill((0, 100, 200))
    stats_lines = []
    total_sim_time = sim.current_time
    stats_lines.append(f"Total Simulation Time: {total_sim_time:.1f} s")
    stats_lines.append("")
    color_names = {
        (0, 255, 0): "Green",
        (255, 255, 0): "Yellow",
        (128, 128, 128): "Gray",
        (0, 0, 0): "Black",
        (128, 0, 128): "Purple"
    }
    for s in ships:
        dx = s.dest_x - s.source_x
        dy = s.dest_y - s.source_y
        distance = math.hypot(dx, dy)
        optimal_time = (distance / s.speed * 3600) if s.speed > 0 else 0
        diff = total_sim_time - optimal_time
        ship_label = color_names.get(s.color, s.name)
        stats_lines.append(f"{ship_label}:")
        stats_lines.append(f"  Optimal Time: {optimal_time:.1f} s")
        stats_lines.append(f"  Extra Time: {diff:.1f} s")
        stats_lines.append("")
    adjustments = len(sim.ui_log) if hasattr(sim, "ui_log") else 0
    stats_lines.append(f"Heading Adjustments: {adjustments}")
    stats_lines.append("")
    stats_lines.append("Classifications:")
    stats_lines.append("  Head-on: 0")
    stats_lines.append("  Crossing: 0")
    stats_lines.append("  Overtaking: 0")
    y_offset = 50
    for line in stats_lines:
        line_surf = font.render(line, True, (255, 255, 255))
        screen.blit(line_surf, (50, y_offset))
        y_offset += line_surf.get_height() + 10
    btn_back_stats = pygame.Rect(50, 500, 120, 40)
    btn_main_menu = pygame.Rect(200, 500, 120, 40)
    draw_button(screen, btn_back_stats, "Back", font)
    draw_button(screen, btn_main_menu, "Main Menu", font)
    return btn_back_stats, btn_main_menu

###############################################################################
# 5) Main Program
###############################################################################
def main():
    pygame.init()
    # Start with an initial size (resizable)
    initial_size = (800, 600)
    screen = pygame.display.set_mode(initial_size, pygame.RESIZABLE)
    pygame.display.set_caption("SeaSafe Simulator")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    global stats_window, compare_mode, stats_mode
    compare_mode = False
    stats_mode = False

    try:
        sea_bg = pygame.image.load("./images/sea_bg.png").convert()
    except:
        sea_bg = pygame.Surface((800, 600))
        sea_bg.fill((0, 100, 200))
    try:
        logo_img = pygame.image.load("./images/logo.png").convert_alpha()
    except:
        logo_img = pygame.Surface((200, 100), pygame.SRCALPHA)
        pygame.draw.rect(logo_img, (255,255,255,180), logo_img.get_rect())
    # Initially scale the logo by a factor of 2
    scale_factor = 2
    new_logo_width = int(logo_img.get_width() * scale_factor)
    new_logo_height = int(logo_img.get_height() * scale_factor)
    logo_img = pygame.transform.scale(logo_img, (new_logo_width, new_logo_height))
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
                scenario_data["map_size"] = data.get("map_size", 6.0)
                scenario_data["safe_distance"] = data.get("safe_distance", 0.2)
                scenario_data["heading_range"] = data.get("heading_range", 40)
                scenario_data["heading_step"] = data.get("heading_step", 1)
                scenario_data["time_step"] = data.get("time_step", 30)
                scenario_data["ships"] = data.get("ships", [])
                return True
            except:
                return False
        return False

    font_small = pygame.font.SysFont(None, 24)
    box_map_size = TextBox((300, 100, 120, 30), font, "6")
    box_safe_dist = TextBox((300, 150, 120, 30), font, "0.2")
    box_search_rng = TextBox((300, 200, 120, 30), font, "40")
    box_search_step = TextBox((300, 250, 120, 30), font, "1")
    box_time_step = TextBox((300, 300, 120, 30), font, "30")
    box_num_ships = TextBox((300, 350, 120, 30), font, "1")
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
    scenario_finished = False

    while running:
        dt = clock.tick(30) / 1000.0
        # Get all events once per frame.
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)

        current_size = screen.get_size()

        if current_state in (STATE_MAIN_MENU, STATE_AUTO_MODE, STATE_MANUAL_SCENARIO, STATE_MANUAL_SHIP_SETUP):
            # Scale the background to fill the window
            scaled_bg = pygame.transform.scale(sea_bg, current_size)
            sea_scroll_x = draw_scrolling_bg(screen, scaled_bg, sea_scroll_x, sea_scroll_speed, dt)

        # --------------------- STATE: MAIN MENU ---------------------
        if current_state == STATE_MAIN_MENU:
            scale_x, scale_y = get_scale_factors(STATE_MAIN_MENU, current_size)
            new_logo_width_scaled = int(new_logo_width * scale_x)
            new_logo_height_scaled = int(new_logo_height * scale_y)
            scaled_logo = pygame.transform.scale(logo_img, (new_logo_width_scaled, new_logo_height_scaled))
            logo_x = (current_size[0] - new_logo_width_scaled) // 2
            logo_y = int(30 * scale_y)
            screen.blit(scaled_logo, (logo_x, logo_y))
            btn_width = int(200 * scale_x)
            btn_height = int(50 * scale_y)
            btn_manual = pygame.Rect((current_size[0] - btn_width) // 2, int(250 * scale_y), btn_width, btn_height)
            btn_auto = pygame.Rect((current_size[0] - btn_width) // 2, int(340 * scale_y), btn_width, btn_height)
            btn_exit = pygame.Rect((current_size[0] - btn_width) // 2, int(430 * scale_y), btn_width, btn_height)
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_manual.collidepoint(event.pos):
                        current_state = STATE_MANUAL_SCENARIO
                    elif btn_auto.collidepoint(event.pos):
                        current_state = STATE_AUTO_MODE
                    elif btn_exit.collidepoint(event.pos):
                        running = False
            draw_button(screen, btn_manual, "Manual Mode", font, color=(0,100,180))
            draw_button(screen, btn_auto, "Automatic Mode", font, color=(0,100,180))
            draw_button(screen, btn_exit, "Exit", font, color=(0,100,180))
            pygame.display.flip()

        # --------------------- STATE: AUTO MODE ---------------------
        elif current_state == STATE_AUTO_MODE:
            scale_x, scale_y = get_scale_factors(STATE_AUTO_MODE, current_size)
            overlay = pygame.Surface(current_size, pygame.SRCALPHA)
            overlay.fill((0,0,0,100))
            screen.blit(overlay, (0,0))
            btn_back = pygame.Rect(int(50*scale_x), int(500*scale_y), int(100*scale_x), int(40*scale_y))
            btn_load = pygame.Rect(int(300*scale_x), int(200*scale_y), int(200*scale_x), int(50*scale_y))
            btn_start = pygame.Rect(int(300*scale_x), int(300*scale_y), int(200*scale_x), int(50*scale_y))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_load.collidepoint(event.pos):
                        ok = load_scenario_from_json()
                        if not ok:
                            warning_msg_auto = "Error: Invalid or non-JSON file!"
                            automatic_loaded_ok = False
                        else:
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
            draw_button(screen, btn_back, "Back", font)
            draw_button(screen, btn_load, "Load JSON", font)
            draw_button(screen, btn_start, "Start", font)
            if warning_msg_auto:
                msg_surf = font.render(warning_msg_auto, True, (255,0,0))
                screen.blit(msg_surf, (int(200*scale_x), int(400*scale_y)))
            pygame.display.flip()

        # --------------------- STATE: MANUAL SCENARIO ---------------------
        elif current_state == STATE_MANUAL_SCENARIO:
            scale_x, scale_y = get_scale_factors(STATE_MANUAL_SCENARIO, current_size)
            overlay = pygame.Surface(current_size, pygame.SRCALPHA)
            overlay.fill((0,0,0,100))
            screen.blit(overlay, (0,0))
            btn_back = pygame.Rect(int(50*scale_x), int(500*scale_y), int(100*scale_x), int(40*scale_y))
            btn_next = pygame.Rect(int(600*scale_x), int(500*scale_y), int(100*scale_x), int(40*scale_y))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_next.collidepoint(event.pos):
                        scenario_data["map_size"] = box_map_size.get_float(6.0)
                        scenario_data["safe_distance"] = box_safe_dist.get_float(0.2)
                        scenario_data["heading_range"] = box_search_rng.get_float(40)
                        scenario_data["heading_step"] = box_search_step.get_float(1)
                        scenario_data["time_step"] = box_time_step.get_float(30)
                        scenario_data["num_ships"] = box_num_ships.get_int(1)
                        ship_boxes = create_ship_boxes(scenario_data["num_ships"])
                        scenario_data["ship_boxes"] = ship_boxes
                        current_state = STATE_MANUAL_SHIP_SETUP
                box_map_size.update_rect(scale_x, scale_y)
                box_safe_dist.update_rect(scale_x, scale_y)
                box_search_rng.update_rect(scale_x, scale_y)
                box_search_step.update_rect(scale_x, scale_y)
                box_time_step.update_rect(scale_x, scale_y)
                box_num_ships.update_rect(scale_x, scale_y)
                for event in events:
                    box_map_size.handle_event(event)
                    box_safe_dist.handle_event(event)
                    box_search_rng.handle_event(event)
                    box_search_step.handle_event(event)
                    box_time_step.handle_event(event)
                    box_num_ships.handle_event(event)
            label = font.render("Map Size:", True, (255,255,255))
            screen.blit(label, (box_map_size.rect.x - label.get_width() - 5, box_map_size.rect.y))
            label = font.render("SafeDist:", True, (255,255,255))
            screen.blit(label, (box_safe_dist.rect.x - label.get_width() - 5, box_safe_dist.rect.y))
            label = font.render("SearchRange:", True, (255,255,255))
            screen.blit(label, (box_search_rng.rect.x - label.get_width() - 5, box_search_rng.rect.y))
            label = font.render("SearchStep:", True, (255,255,255))
            screen.blit(label, (box_search_step.rect.x - label.get_width() - 5, box_search_step.rect.y))
            label = font.render("TimeStep:", True, (255,255,255))
            screen.blit(label, (box_time_step.rect.x - label.get_width() - 5, box_time_step.rect.y))
            label = font.render("#Ships:", True, (255,255,255))
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

        # --------------------- STATE: MANUAL SHIP SETUP ---------------------
        elif current_state == STATE_MANUAL_SHIP_SETUP:
            scale_x, scale_y = get_scale_factors(STATE_MANUAL_SHIP_SETUP, current_size)
            overlay = pygame.Surface(current_size, pygame.SRCALPHA)
            overlay.fill((0,0,0,100))
            screen.blit(overlay, (0,0))
            btn_back = pygame.Rect(int(50*scale_x), int(600*scale_y), int(120*scale_x), int(40*scale_y))
            btn_start = pygame.Rect(int(250*scale_x), int(600*scale_y), int(120*scale_x), int(40*scale_y))
            local_ship_boxes = scenario_data.get("ship_boxes", [])
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MANUAL_SCENARIO
                    elif btn_start.collidepoint(event.pos):
                        scenario_data["ships"] = []
                        for i, row in enumerate(local_ship_boxes):
                            speedBox, startBox, destBox, lenBox, widBox = row
                            speed = speedBox.get_float(20)
                            sx, sy = parse_xy(startBox.get_str())
                            dx_, dy_ = parse_xy(destBox.get_str())
                            length_ = lenBox.get_float(300)
                            width_ = widBox.get_float(50)
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
                        current_state = STATE_SIMULATION
                for row in local_ship_boxes:
                    for tb in row:
                        tb.update_rect(scale_x, scale_y)
                        for event in events:
                            tb.handle_event(event)
            header_surf = font.render("Speed | Start(x,y) | Dest(x,y) | Length(m) | Width(m)", True, (255,255,255))
            screen.blit(header_surf, (int(80*scale_x), int(90*scale_y)))
            y = 150
            for i, row in enumerate(local_ship_boxes):
                label_ship = font.render(f"Ship {i+1} ", True, (255,255,255))
                screen.blit(label_ship, (int(10*scale_x), int(y*scale_y)+int(10*scale_y)))
                for tb in row:
                    tb.draw(screen)
                y += 60
            draw_button(screen, btn_back, "Back", font)
            draw_button(screen, btn_start, "Start", font)
            # Draw Minimap in STATE_MANUAL_SHIP_SETUP
            minimap_pos = (int(700*scale_x), int(20*scale_y))
            minimap_size = int(140*scale_x)  # square minimap
            dummy_ships = []
            for i, row in enumerate(local_ship_boxes):
                startBox = row[1]
                destBox = row[2]
                sx, sy = parse_xy(startBox.get_str())
                dx, dy = parse_xy(destBox.get_str())
                dummy_ship = type("DummyShip", (), {})()
                dummy_ship.x = sx
                dummy_ship.y = sy
                dummy_ship.dest_x = dx
                dummy_ship.dest_y = dy
                dummy_ship.color = ship_colors[i % len(ship_colors)]
                dummy_ships.append(dummy_ship)
            draw_minimap(screen, dummy_ships, scenario_data["map_size"], minimap_pos, minimap_size)
            pygame.display.flip()

        # --------------------- STATE: SIMULATION ---------------------
        elif current_state == STATE_SIMULATION:
            # *** NEW: Clear the entire screen to hide previous state (e.g., main menu) ***
            screen.fill((130,180,255))
            # Compute a uniform scale factor based on the simulation base resolution (880x920)
            base_sim_w, base_sim_h = BASE_RESOLUTIONS[STATE_SIMULATION]
            current_w, current_h = current_size
            scale = min(current_w / base_sim_w, current_h / base_sim_h)
            # Center the simulation area inside the window.
            sim_area_w = int(base_sim_w * scale)
            sim_area_h = int(base_sim_h * scale)
            offset_sim_x = (current_w - sim_area_w) // 2
            offset_sim_y = (current_h - sim_area_h) // 2

            # Define the simulation layout relative to the base layout scaled by 'scale'
            left_label_margin = int(60 * scale)
            top_margin = int(20 * scale)
            map_width = int(800 * scale)
            map_height = int(800 * scale)
            bottom_margin = int(60 * scale)
            ui_panel_height = int(40 * scale)
            right_margin = int(20 * scale)
            # (Optional) Draw a border for the simulation area
            simulation_area_rect = pygame.Rect(offset_sim_x, offset_sim_y, sim_area_w, sim_area_h)
            pygame.draw.rect(screen, (130,180,255), simulation_area_rect)
            # The map (grid) rectangle is drawn relative to the simulation area:
            map_rect = pygame.Rect(offset_sim_x + left_label_margin, offset_sim_y + top_margin, map_width, map_height)
            # Create a scaled font for simulation state
            sim_font = pygame.font.SysFont(None, int(28 * scale))
            # Compute nautical miles to pixels based on the map width and the scenario's map size.
            nm_to_px = map_width / scenario_data["map_size"]
            # Define UI buttons (in the UI panel area, which is below the map)
            ui_panel_y = offset_sim_y + top_margin + map_height + bottom_margin
            btn_back_sim = pygame.Rect(offset_sim_x + left_label_margin + int(10*scale), ui_panel_y + int(5*scale), int(100*scale), int(35*scale))
            btn_replay_sim = pygame.Rect(offset_sim_x + left_label_margin + int(120*scale), ui_panel_y + int(5*scale), int(100*scale), int(35*scale))
            btn_compare = pygame.Rect(offset_sim_x + left_label_margin + int(230*scale), ui_panel_y + int(5*scale), int(100*scale), int(35*scale))
            btn_next = pygame.Rect(offset_sim_x + left_label_margin + int(340*scale), ui_panel_y + int(5*scale), int(100*scale), int(35*scale))
            # Process events for simulation state.
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back_sim.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                        sim = None
                        paused = False
                        scenario_finished = False
                        compare_mode = False
                    elif btn_replay_sim.collidepoint(event.pos):
                        sim = None
                        paused = False
                        scenario_finished = False
                        compare_mode = False
                    elif btn_compare.collidepoint(event.pos) and scenario_finished:
                        compare_mode = not compare_mode
                    elif btn_next.collidepoint(event.pos) and scenario_finished:
                        current_state = STATE_STATS
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        paused = not paused

            # If the state changed (for example via the Back button), skip further drawing.
            if current_state != STATE_SIMULATION:
                pygame.display.flip()
                continue

            # Initialize simulation if not yet done.
            if sim is None:
                loaded_ships = []
                for i, sdata in enumerate(scenario_data["ships"]):
                    sname = sdata.get("name", f"Ship{i+1}")
                    heading = sdata.get("heading", 0.0)
                    speed = sdata.get("speed", 20.0)
                    sx = sdata.get("start_x", 0.0)
                    sy = sdata.get("start_y", 0.0)
                    dx_ = sdata.get("dest_x", 5.0)
                    dy_ = sdata.get("dest_y", 5.0)
                    length_ = sdata.get("length_m", 300)
                    width_ = sdata.get("width_m", 50)
                    ship_obj = Ship(sname, sx, sy, heading, speed, dx_, dy_, length_, width_)
                    ship_obj.color = ship_colors[i % len(ship_colors)]
                    ship_obj.trail = []
                    ship_obj.source_x = sx
                    ship_obj.source_y = sy
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
                scenario_finished = False
                paused = False
                compare_mode = False

            if not scenario_finished and sim is not None and not paused:
                sim.step(debug=False)
                for sh in ships:
                    sh.trail.append((sh.x, sh.y))
                if sim.all_ships_arrived():
                    scenario_finished = True

            # Draw the grid and ships using coordinates relative to the simulation area.
            draw_grid(screen, map_rect, scenario_data["map_size"], nm_to_px, tick_step=0.5)
            for s in ships:
                draw_ship_trail(screen, s, nm_to_px, map_height,
                                offset_x=offset_sim_x + left_label_margin,
                                offset_y=offset_sim_y + top_margin)
                draw_safety_circle(screen, s, sim.safe_distance, nm_to_px, map_height,
                                   offset_x=offset_sim_x + left_label_margin,
                                   offset_y=offset_sim_y + top_margin)
                draw_ship_rect(screen, s, nm_to_px, map_height,
                               offset_x=offset_sim_x + left_label_margin,
                               offset_y=offset_sim_y + top_margin)
            for s in ships:
                dest_x_screen = offset_sim_x + left_label_margin + int(s.dest_x * nm_to_px)
                dest_y_screen = offset_sim_y + top_margin + map_height - int(s.dest_y * nm_to_px)
                draw_star(screen, (dest_x_screen, dest_y_screen), int(8 * scale), s.color)
            
            # Draw simulation state labels (time step, instructions, paused message) relative to the simulation area.
            time_label = sim_font.render(f"Current Time Step: {sim.current_time}s", True, (0,0,0))
            screen.blit(time_label, (offset_sim_x + left_label_margin + int(10*scale), offset_sim_y + top_margin + int(10*scale)))
            space_label = sim_font.render("Press SPACE to Pause/Resume", True, (200,0,0))
            screen.blit(space_label, (offset_sim_x + left_label_margin + int(10*scale), offset_sim_y + top_margin + int(30*scale)))
            if paused:
                pause_text = sim_font.render("PAUSED", True, (255,0,0))
                screen.blit(pause_text, (offset_sim_x + left_label_margin + int(10*scale), offset_sim_y + top_margin + int(50*scale)))
            if scenario_finished:
                if not compare_mode:
                    finish_text = sim_font.render("Scenario finished - all ships reached destinations!", True, (0,150,0))
                    fx = offset_sim_x + left_label_margin + (map_width - finish_text.get_width()) // 2
                    fy = offset_sim_y + top_margin + map_height//2 - finish_text.get_height()//2
                    screen.blit(finish_text, (fx,fy))
                else:
                    for s in ships:
                        start_pos = (offset_sim_x + left_label_margin + int(s.source_x * nm_to_px),
                                     offset_sim_y + top_margin + map_height - int(s.source_y * nm_to_px))
                        end_pos = (offset_sim_x + left_label_margin + int(s.dest_x * nm_to_px),
                                   offset_sim_y + top_margin + map_height - int(s.dest_y * nm_to_px))
                        draw_dashed_line(screen, s.color, start_pos, end_pos, dash_length=int(5*scale), space_length=int(10*scale))
            # Draw grid labels relative to the simulation area.
            draw_y_axis_labels_in_margin(screen, pygame.Rect(offset_sim_x, offset_sim_y + top_margin, left_label_margin, map_height),
                                         scenario_data["map_size"], sim_font, tick_step=0.5)
            draw_x_axis_labels_in_margin(screen, pygame.Rect(offset_sim_x + left_label_margin, offset_sim_y + top_margin + map_height, map_width, bottom_margin),
                                         scenario_data["map_size"], sim_font, tick_step=0.5)
            pygame.draw.line(screen, (200,200,200),
                             (offset_sim_x + left_label_margin, offset_sim_y + top_margin + map_height),
                             (offset_sim_x + left_label_margin + map_width, offset_sim_y + top_margin + map_height), 1)
            ui_panel_rect = pygame.Rect(offset_sim_x + left_label_margin, ui_panel_y, map_width, ui_panel_height)
            pygame.draw.rect(screen, (60,60,60), ui_panel_rect)
            draw_button(screen, btn_back_sim, "Back", sim_font)
            draw_button(screen, btn_replay_sim, "Replay", sim_font)
            if scenario_finished:
                draw_button(screen, btn_compare, "Compare", sim_font)
                draw_button(screen, btn_next, "Next", sim_font)
            pygame.display.flip()
            clock.tick(3)

        # --------------------- STATE: STATS ---------------------
        elif current_state == STATE_STATS:
            scale_x, scale_y = get_scale_factors(STATE_STATS, current_size)
            screen.fill((0,100,200))
            btn_back_stats, btn_main_menu = draw_stats_screen(screen, sim, ships, font)
            btn_back_stats_scaled = pygame.Rect(int(50*scale_x), int(500*scale_y), int(120*scale_x), int(40*scale_y))
            btn_main_menu_scaled = pygame.Rect(int(200*scale_x), int(500*scale_y), int(120*scale_x), int(40*scale_y))
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back_stats_scaled.collidepoint(event.pos):
                        current_state = STATE_SIMULATION
                    elif btn_main_menu_scaled.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                        sim = None
                        paused = False
                        scenario_finished = False
                        compare_mode = False
            pygame.display.flip()
            clock.tick(3)
        else:
            running = False
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
