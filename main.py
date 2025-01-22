# main.py

import pygame
import sys
import math
import json
import tkinter as tk
import tkinter.filedialog as fd

# Import your collision logic from logic.py
# logic.py must define Ship, Simulator, and get_collisions_with_roles in Simulator
from logic import Ship, Simulator

################################################################################
# 1) State Constants
################################################################################
STATE_MAIN_MENU         = 1
STATE_AUTO_MODE         = 2
STATE_MANUAL_SCENARIO   = 3
STATE_MANUAL_SHIP_SETUP = 4
STATE_SIMULATION        = 5

################################################################################
# 2) TextBox Class for UI
################################################################################
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
        color = (0, 200, 0) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)
        txt_surf = self.font.render(self.text, True, (255,255,255))
        screen.blit(txt_surf, (self.rect.x+5, self.rect.y+5))

    def get_str(self):
        return self.text.strip()

    def get_float(self, default=0.0):
        """Try parse float from the text, else return default."""
        try:
            return float(self.text)
        except ValueError:
            return default

    def get_int(self, default=0):
        """Try parse int from the text, else return default."""
        try:
            return int(self.text)
        except ValueError:
            return default


################################################################################
# 3) Helper Functions (Buttons, XY parsing)
################################################################################
def draw_button(screen, rect, text, font, color=(0,0,200)):
    pygame.draw.rect(screen, color, rect)
    label = font.render(text, True, (255,255,255))
    lx = rect.x + (rect.width - label.get_width())/2
    ly = rect.y + (rect.height - label.get_height())/2
    screen.blit(label, (lx, ly))

def parse_xy(s):
    """
    Parse a string like '3,2' or '3.0 2.5' -> (3.0, 2.5).
    Fallback to (0,0) if parsing fails.
    """
    s = s.replace(',', ' ')
    parts = s.split()
    if len(parts) == 2:
        try:
            x = float(parts[0])
            y = float(parts[1])
            return (x,y)
        except:
            pass
    return (0.0, 0.0)


################################################################################
# 4) Drawing Ships in Simulation
################################################################################
def draw_ship(screen, ship, nm_to_px, screen_height):
    """
    Flip y-axis so 0,0 is bottom-left, then draw a rectangle for the ship.
    We'll rotate by the ship.heading (assuming 0=East, angles grow CCW in logic).
    In PyGame, +angle rotates sprite clockwise.
    """
    length_nm = ship.length_m / 1852.0
    width_nm  = ship.width_m  / 1852.0
    length_px = length_nm * nm_to_px
    width_px  = width_nm  * nm_to_px

    x_screen = ship.x * nm_to_px
    y_screen = screen_height - (ship.y * nm_to_px)

    surf_l = max(1, int(length_px))
    surf_w = max(1, int(width_px))
    ship_surf = pygame.Surface((surf_l, surf_w), pygame.SRCALPHA)
    ship_surf.fill((255,255,255))

    angle_for_pygame = ship.heading
    rotated = pygame.transform.rotate(ship_surf, angle_for_pygame)
    rect = rotated.get_rect()
    rect.center = (x_screen, y_screen)
    screen.blit(rotated, rect)


def draw_ship_role(screen, ship, role_text, nm_to_px, screen_height, font):
    """
    Draw "Give-Way" or "Stand-On" near the ship if role_text is not empty.
    """
    if not role_text:
        return
    x_screen = ship.x * nm_to_px
    y_screen = screen_height - (ship.y * nm_to_px)
    label_surf = font.render(role_text, True, (255,255,255))
    screen.blit(label_surf, (x_screen - label_surf.get_width()/2, y_screen + 10))


################################################################################
# 5) Main Program with Multi-Screen Flow
################################################################################
def main():
    pygame.init()
    pygame.display.set_caption("Collision Avoidance - Menu")
    screen = pygame.display.set_mode((800,600))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont(None, 28)

    current_state = STATE_MAIN_MENU
    running = True

    # We'll store scenario data in a dict
    scenario_data = {
        "map_size": 6.0,
        "safe_distance": 0.2,
        "heading_range": 40.0,
        "heading_step": 1.0,
        "time_step": 30.0,
        "ships": [],
        "num_ships": 1
    }

    # Automatic mode
    automatic_loaded_ok = False

    # For building simulator
    sim = None
    ships = []
    ship_roles = {}
    SIM_W, SIM_H = 800, 800
    nm_to_px = 100.0

    ############################################################################
    #  A) Helper: load JSON scenario
    ############################################################################
    def load_scenario_from_json():
        root = tk.Tk()
        root.withdraw()
        file_path = fd.askopenfilename(filetypes=[("JSON Files","*.json")])
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
                print("Error loading JSON.")
        return False

    ############################################################################
    #  B) Sub-screens for Manual Mode
    ############################################################################
    # 1) Manual Scenario Screen
    box_map_size    = TextBox((300,100,120,30), font, "6")
    box_safe_dist   = TextBox((300,150,120,30), font, "0.2")
    box_search_rng  = TextBox((300,200,120,30), font, "40")
    box_search_step = TextBox((300,250,120,30), font, "1")
    box_time_step   = TextBox((300,300,120,30), font, "30")
    box_num_ships   = TextBox((300,350,120,30), font, "1")

    # We'll create the dynamic "ship setup" boxes once we know num_ships
    ship_boxes = []  # each sublist: [speedBox, startBox, destBox, lengthBox, widthBox]

    def create_ship_boxes(num):
        # We'll create a row for each ship
        # row => 5 text boxes => speed, start(x,y), dest(x,y), length, width
        new_list = []
        start_y = 150
        for i in range(num):
            row = []
            # speed
            row.append(TextBox((50, start_y, 80, 30), font, "20"))
            # start(x,y)
            row.append(TextBox((150, start_y, 100, 30), font, "0,0"))
            # dest(x,y)
            row.append(TextBox((270, start_y, 100, 30), font, "5,5"))
            # length
            row.append(TextBox((390, start_y, 80, 30), font, "300"))
            # width
            row.append(TextBox((490, start_y, 80, 30), font, "50"))

            new_list.append(row)
            start_y += 60
        return new_list

    ############################################################################
    #  C) Main Loop with States
    ############################################################################
    while running:
        if current_state == STATE_MAIN_MENU:
            # Main Menu: 3 buttons => Manual, Automatic, Exit
            screen.fill((50,50,50))

            btn_manual = pygame.Rect(300, 200, 200, 50)
            btn_auto   = pygame.Rect(300, 300, 200, 50)
            btn_exit   = pygame.Rect(300, 400, 200, 50)

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

            draw_button(screen, btn_manual, "Manual Mode", font)
            draw_button(screen, btn_auto,   "Automatic Mode", font)
            draw_button(screen, btn_exit,   "Exit", font)
            pygame.display.flip()
            clock.tick(30)

        elif current_state == STATE_AUTO_MODE:
            # Automatic Mode: 2 buttons => Load JSON, Start, plus Back
            screen.fill((60,60,60))

            btn_back    = pygame.Rect(50, 500, 100, 40)
            btn_load    = pygame.Rect(300, 200, 200, 50)
            btn_start   = pygame.Rect(300, 300, 200, 50)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_load.collidepoint(event.pos):
                        # Load JSON
                        ok = load_scenario_from_json()
                        automatic_loaded_ok = ok
                    elif btn_start.collidepoint(event.pos):
                        # if loaded ok, proceed to sim
                        if automatic_loaded_ok and len(scenario_data["ships"])>0:
                            current_state = STATE_SIMULATION
                        else:
                            print("No valid JSON loaded or no ships in scenario!")

            draw_button(screen, btn_back,  "Back", font)
            draw_button(screen, btn_load,  "Load JSON", font)
            draw_button(screen, btn_start, "Start", font)

            pygame.display.flip()
            clock.tick(30)

        elif current_state == STATE_MANUAL_SCENARIO:
            screen.fill((70,70,70))

            btn_back = pygame.Rect(50,500,100,40)
            btn_next = pygame.Rect(600,500,100,40)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        current_state = STATE_MAIN_MENU
                    elif btn_next.collidepoint(event.pos):
                        # parse scenario
                        scenario_data["map_size"]      = box_map_size.get_float(6.0)
                        scenario_data["safe_distance"] = box_safe_dist.get_float(0.2)
                        scenario_data["heading_range"] = box_search_rng.get_float(40)
                        scenario_data["heading_step"]  = box_search_step.get_float(1)
                        scenario_data["time_step"]     = box_time_step.get_float(30)
                        scenario_data["num_ships"]     = box_num_ships.get_int(1)

                        # create dynamic boxes for the ships
                        ship_boxes = create_ship_boxes(scenario_data["num_ships"])
                        # store them in scenario_data to access in the next state
                        scenario_data["ship_boxes"] = ship_boxes

                        current_state = STATE_MANUAL_SHIP_SETUP

                box_map_size.handle_event(event)
                box_safe_dist.handle_event(event)
                box_search_rng.handle_event(event)
                box_search_step.handle_event(event)
                box_time_step.handle_event(event)
                box_num_ships.handle_event(event)

            # draw text boxes
            # manual labeling
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
            clock.tick(30)

        elif current_state == STATE_MANUAL_SHIP_SETUP:
            # Possibly enlarge the window
            screen = pygame.display.set_mode((900,700))
            pygame.display.set_caption("Ship Setup")
            screen.fill((80,80,80))

            btn_back  = pygame.Rect(50, 600, 120, 40)
            btn_start = pygame.Rect(250, 600, 120, 40)

            ship_boxes = scenario_data.get("ship_boxes", [])
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if btn_back.collidepoint(event.pos):
                        # revert window
                        screen = pygame.display.set_mode((800,600))
                        pygame.display.set_caption("Collision Avoidance - Menu")
                        current_state = STATE_MANUAL_SCENARIO
                    elif btn_start.collidepoint(event.pos):
                        # parse all ship boxes => scenario_data["ships"]
                        scenario_data["ships"] = []
                        for i, row in enumerate(ship_boxes):
                            # row => [speedBox, startBox, destBox, lenBox, widBox]
                            speedBox, startBox, destBox, lenBox, widBox = row
                            speed = speedBox.get_float(20)
                            (sx, sy) = parse_xy(startBox.get_str())
                            (dx_, dy_)= parse_xy(destBox.get_str())
                            length = lenBox.get_float(300)
                            width  = widBox.get_float(50)

                            # auto compute heading from (sx, sy)->(dx_, dy_)
                            heading = 0.0
                            dxval = dx_ - sx
                            dyval = dy_ - sy
                            if abs(dxval)>1e-7 or abs(dyval)>1e-7:
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
                                "length_m": length,
                                "width_m": width
                            })

                        # revert window for simulation
                        screen = pygame.display.set_mode((800,600))
                        pygame.display.set_caption("Collision Avoidance - Menu")
                        current_state = STATE_SIMULATION

                for row in ship_boxes:
                    for tb in row:
                        tb.handle_event(event)

            # draw header
            header_surf = font.render("Speed  |  Start(x,y)  |  Dest(x,y)  |  Length(m)  |  Width(m)", True, (255,255,255))
            screen.blit(header_surf, (50, 100))

            # draw each row
            y = 150
            for i, row in enumerate(ship_boxes):
                label_ship = font.render(f"Ship {i+1}", True, (255,255,255))
                screen.blit(label_ship, (10, y+5))
                for tb in row:
                    tb.draw(screen)
                y += 60

            draw_button(screen, btn_back,  "Back", font)
            draw_button(screen, btn_start, "Start", font)
            pygame.display.flip()
            clock.tick(30)

        elif current_state == STATE_SIMULATION:
            # If sim not built yet, do so
            if sim is None:
                # build from scenario_data
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
                    wid_    = sdata.get("width_m", 50)

                    ship_obj = Ship(sname, sx, sy, heading, speed, dx_, dy_, length_, wid_)
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

                # open new 800x800 for simulation
                screen = pygame.display.set_mode((SIM_W, SIM_H))
                pygame.display.set_caption("Collision Avoidance - Simulation")
                nm_to_px = SIM_W / scenario_data["map_size"]

            # run discrete steps
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # 1) get collisions + roles
            collision_info = sim.get_collisions_with_roles()
            for sh in ships:
                ship_roles[sh.name] = ""
            for (dist_cpa, i, j, encounter, roleA, roleB) in collision_info:
                if ship_roles[ships[i].name] == "":
                    ship_roles[ships[i].name] = roleA
                if ship_roles[ships[j].name] == "":
                    ship_roles[ships[j].name] = roleB

            # 2) step
            sim.step()

            # 3) draw
            screen.fill((130,180,255))
            for s in ships:
                draw_ship(screen, s, nm_to_px, SIM_H)
                # draw_ship_role(screen, s, ship_roles[s.name], nm_to_px, SIM_H, font)

            pygame.display.flip()
            clock.tick(2)  # 2 FPS => discrete steps

            # end if all arrived
            if sim.all_ships_arrived():
                running = False

        else:
            running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
