# main.py

import pygame
import sys

# Import the necessary classes/methods from logic.py
from logic import Ship, Simulator  # Make sure logic.py has get_collisions_with_roles() in Simulator!

#############################################################################
# 1. TextBox Class for PyGame Menu Input
#############################################################################
class TextBox:
    def __init__(self, rect, font, prompt="", initial_text=""):
        self.rect = pygame.Rect(rect)
        self.font = font
        self.prompt = prompt
        self.text = initial_text
        self.active = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_RETURN:
                pass  # Could do something on Enter
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, screen):
        color = (0, 200, 0) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)

        # Draw prompt text
        prompt_surf = self.font.render(self.prompt, True, (255,255,255))
        screen.blit(prompt_surf, (self.rect.x - prompt_surf.get_width() - 10, self.rect.y))

        # Draw typed text
        text_surf = self.font.render(self.text, True, (255,255,255))
        screen.blit(text_surf, (self.rect.x+5, self.rect.y+5))

    def get_value(self):
        """Try to parse the text as float, else return string."""
        try:
            return float(self.text)
        except ValueError:
            return self.text

#############################################################################
# 2. Drawing Functions: Ship Rectangle + Role Label
#############################################################################
def draw_ship(screen, ship, nm_to_px):
    """
    Draw the ship as a rotated rectangle, based on heading and size.
    Ship dimensions in meters => convert to NM => then to pixels.
    """
    import math, pygame

    # Convert ship length/width from meters to NM
    length_nm = ship.length_m / 1852.0
    width_nm  = ship.width_m  / 1852.0

    # Convert NM to px
    length_px = length_nm * nm_to_px
    width_px  = width_nm  * nm_to_px

    # Center position in px
    cx = ship.x * nm_to_px
    cy = ship.y * nm_to_px

    # Create a small surface for the ship rectangle
    surf_w = max(1, int(width_px))
    surf_l = max(1, int(length_px))
    ship_surf = pygame.Surface((surf_l, surf_w), pygame.SRCALPHA)

    # Fill it white
    ship_surf.fill((255, 255, 255))

    # PyGame rotation is clockwise for positive angles;
    # Our headings increase counterclockwise => rotate by -ship.heading
    angle_for_pygame = -ship.heading

    rotated = pygame.transform.rotate(ship_surf, angle_for_pygame)
    rect = rotated.get_rect()
    rect.center = (cx, cy)

    screen.blit(rotated, rect)


def draw_ship_role(screen, ship, role_text, nm_to_px, font):
    """
    Draw the collision-avoidance role (Give-Way/Stand-On/etc.) near the ship.
    """
    if not role_text:
        return

    x_px = ship.x * nm_to_px
    y_px = ship.y * nm_to_px

    label_surf = font.render(role_text, True, (255,255,255))
    # Place the label a bit below the ship
    screen.blit(label_surf, (x_px - label_surf.get_width()/2, y_px + 10))

#############################################################################
# 3. Main Program: Menu + Simulation
#############################################################################
def main():
    pygame.init()
    font = pygame.font.SysFont(None, 28)

    # ----------------- MENU SCREEN -----------------
    menu_screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Collision Avoidance - Menu")

    clock = pygame.time.Clock()

    # Prepare text boxes for user inputs
    boxes = [
        TextBox((200, 50, 100, 30), font, "Map Size(NM):", "6"),
        TextBox((200, 100, 100, 30), font, "# Ships:", "2"),
        TextBox((200, 150, 100, 30), font, "SafeDist(NM):", "0.2"),
        TextBox((200, 200, 100, 30), font, "SearchRange:", "40"),
        TextBox((200, 250, 100, 30), font, "SearchStep:", "1"),
        TextBox((200, 300, 100, 30), font, "TimeStep(s):", "30"),
    ]
    start_button = pygame.Rect(200, 400, 150, 40)

    menu_running = True
    while menu_running:
        menu_screen.fill((50,50,50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for tb in boxes:
                tb.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    # User pressed Start => parse inputs => move to sim
                    menu_running = False

        # Draw input boxes
        for tb in boxes:
            tb.draw(menu_screen)

        # Draw Start button
        pygame.draw.rect(menu_screen, (0,0,200), start_button)
        label = font.render("Start Simulation", True, (255,255,255))
        menu_screen.blit(label, (start_button.x+5, start_button.y+5))

        pygame.display.flip()
        clock.tick(30)  # 30 FPS in menu

    # ------------- PARSE INPUTS FROM TEXT BOXES -------------
    map_size        = boxes[0].get_value()  # float
    num_ships       = int(boxes[1].get_value())
    safe_distance   = boxes[2].get_value()
    heading_range   = boxes[3].get_value()
    heading_step    = boxes[4].get_value()
    time_step_sec   = boxes[5].get_value()

    # ------------- CREATE THE SHIPS & SIMULATOR -------------
    # For demonstration, handle 2 ships scenario if user picks "2"
    if num_ships == 2:
        # Example scenario
        shipA = Ship("ShipA", 0.0, 0.0, 45.0, 20.0, 5.0, 5.0, length_m=300, width_m=50)
        shipB = Ship("ShipB", 5.0, 5.0, 225.0, 20.0, 0.0, 0.0, length_m=300, width_m=50)
        ships = [shipA, shipB]
    else:
        # Or create random / other scenarios
        shipA = Ship("ShipA", 0.0, 0.0, 45.0, 20.0, 5.0, 5.0)
        shipB = Ship("ShipB", 5.0, 5.0, 225.0, 20.0, 0.0, 0.0)
        ships = [shipA, shipB]

    sim = Simulator(
        ships = ships,
        time_step = time_step_sec,
        safe_distance = safe_distance,
        heading_search_range = heading_range,
        heading_search_step = heading_step
    )

    # ------------- SIMULATION SCREEN -------------
    sim_screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Collision Avoidance - Simulation")

    # Convert NM to px so entire map_size covers 800px
    nm_to_px = 800.0 / map_size

    # We'll run the simulation at 2 FPS => each frame is 0.5s real time,
    # each sim.step() jumps time_step_sec in the simulation.
    FPS = 2
    fps_clock = pygame.time.Clock()

    # We track each ship's role in a dict => { ship.name: "Give-Way" / "Stand-On" / "" }
    ship_roles = {ship.name: "" for ship in ships}

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # 1) Get collisions + roles BEFORE we step (so we display the roles in the current scenario)
        collision_info = sim.get_collisions_with_roles()  # you must have added this method in logic.py

        # Clear old roles
        for ship in ships:
            ship_roles[ship.name] = ""

        # Fill roles (lowest CPA first => highest priority)
        for (dist_cpa, i, j, encounter, roleA, roleB) in collision_info:
            shA = ships[i]
            shB = ships[j]
            # only set role if not already set
            if ship_roles[shA.name] == "":
                ship_roles[shA.name] = roleA
            if ship_roles[shB.name] == "":
                ship_roles[shB.name] = roleB

        # 2) Step the simulation => headings might change, ships move
        sim.step()

        # 3) Draw the new state
        sim_screen.fill((130, 180, 255))  # lighter blue background
        for s in ships:
            draw_ship(sim_screen, s, nm_to_px)
            draw_ship_role(sim_screen, s, ship_roles[s.name], nm_to_px, font)

        pygame.display.flip()

        # If all ships arrived => end
        if sim.all_ships_arrived():
            running = False

        # 4) Limit frame rate => 2 FPS
        fps_clock.tick(FPS)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
