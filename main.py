# main.py
import pygame
import sys
import math
import numpy as np

from logic import Ship, Simulator

#############################################################################
# A. Minimal TextBox Class for Basic User Input in PyGame
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
                pass  # do nothing special
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            else:
                self.text += event.unicode

    def draw(self, screen):
        color = (0, 200, 0) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)

        prompt_surf = self.font.render(self.prompt, True, (255,255,255))
        screen.blit(prompt_surf, (self.rect.x - prompt_surf.get_width() - 10, self.rect.y))

        text_surf = self.font.render(self.text, True, (255,255,255))
        screen.blit(text_surf, (self.rect.x+5, self.rect.y+5))

    def get_value(self):
        # Try to parse float
        try:
            return float(self.text)
        except ValueError:
            return self.text


#############################################################################
# B. Drawing Ships as Rotated Rectangles (Now WHITE) in PyGame
#############################################################################
def draw_ship(screen, ship, nm_to_px):
    """
    Draw the ship as a rotated rectangle, based on its heading.
    length_m, width_m are in meters => convert to NM => then to px.
    The rectangle is filled white, and rotated to match 'ship.heading'.
    """
    # Convert from meters to NM: 1 NM ~ 1852 m
    length_nm = ship.length_m / 1852.0
    width_nm  = ship.width_m  / 1852.0

    length_px = length_nm * nm_to_px
    width_px  = width_nm  * nm_to_px

    # Position in pixels
    center_x = ship.x * nm_to_px
    center_y = ship.y * nm_to_px

    # Create a surface for the ship rectangle
    surf_width = max(1, int(width_px))
    surf_length = max(1, int(length_px))
    surf = pygame.Surface((surf_length, surf_width), pygame.SRCALPHA)
    
    # Fill white
    surf.fill((255, 255, 255))

    # In math, heading=0 => East, angles inc CCW
    # In pygame.transform.rotate, angle is degrees clockwise
    # => angle_for_pygame = -ship.heading
    angle_for_pygame = -ship.heading

    rotated_surf = pygame.transform.rotate(surf, angle_for_pygame)
    rect = rotated_surf.get_rect()
    rect.center = (center_x, center_y)

    screen.blit(rotated_surf, rect)


#############################################################################
# C. Main Program with "Menu" + "Simulation"
#############################################################################
def main():
    pygame.init()
    font = pygame.font.SysFont(None, 28)

    # Menu screen (800 x 600)
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Collision Avoidance - Menu")

    clock = pygame.time.Clock()

    # A few input boxes
    boxes = [
        TextBox((200,50,100,30), font, "Map Size(NM):", "6"),
        TextBox((200,100,100,30), font, "# Ships:", "2"),
        TextBox((200,150,100,30), font, "SafeDist(NM):", "0.2"),
        TextBox((200,200,100,30), font, "SearchRange:", "40"),
        TextBox((200,250,100,30), font, "SearchStep:", "1"),
        TextBox((200,300,100,30), font, "TimeStep(s):", "30"),
    ]

    start_button = pygame.Rect(200,400,150,40)
    menu_running = True

    while menu_running:
        screen.fill((50,50,50))

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            for tb in boxes:
                tb.handle_event(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    # parse input => start simulation
                    menu_running = False

        # Draw input boxes
        for tb in boxes:
            tb.draw(screen)

        # Draw start button
        pygame.draw.rect(screen, (0,0,200), start_button)
        label = font.render("Start Simulation", True, (255,255,255))
        screen.blit(label, (start_button.x+5, start_button.y+5))

        pygame.display.flip()
        clock.tick(30)  # 30 FPS for menu

    # Get values from text boxes
    map_size        = boxes[0].get_value()       # float
    num_ships       = int(boxes[1].get_value())  # int
    safe_distance   = boxes[2].get_value()
    heading_range   = boxes[3].get_value()
    heading_step    = boxes[4].get_value()
    time_step_sec   = boxes[5].get_value()

    # Build ships. For demonstration, handle if user says "2 ships."
    from logic import Ship
    if num_ships == 2:
        # Example scenario
        shipA = Ship("ShipA", 0.0, 0.0, 45.0, 20.0, 5.0, 5.0, length_m=300, width_m=100)
        shipB = Ship("ShipB", 5.0, 5.0, 225.0, 20.0, 0.0, 0.0, length_m=300, width_m=100)
        ships = [shipA, shipB]
    else:
        # or random scenario / more textboxes for each ship
        ships = [
            Ship("ShipA", 0.0, 0.0, 45.0, 20.0, 5.0, 5.0),
            Ship("ShipB", 5.0, 5.0, 225.0, 20.0, 0.0, 0.0)
        ]

    from logic import Simulator
    sim = Simulator(
        ships = ships,
        time_step = time_step_sec,
        safe_distance = safe_distance,
        heading_search_range = heading_range,
        heading_search_step = heading_step
    )

    # Simulation screen (800 x 800)
    sim_screen = pygame.display.set_mode((800, 800))
    pygame.display.set_caption("Collision Avoidance - Simulation")

    running = True
    fps_clock = pygame.time.Clock()

    # For mapping NM -> px
    nm_to_px = 800.0 / map_size  # entire map_size in NM spans 800 px

    # We'll set a slower discrete pace => 2 frames / sec => 0.5s per frame
    # Each frame = sim.step() => e.g., 30s in sim time
    FPS = 2

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Each frame => do one discrete step
        sim.step()

        # Fill background with sea-like color
        sim_screen.fill((0, 105, 148))  # a shade of ocean blue

        # Draw ships
        for s in sim.ships:
            draw_ship(sim_screen, s, nm_to_px)

        pygame.display.flip()

        # If all arrived, we stop
        if sim.all_ships_arrived():
            running = False

        # Limit to 2 frames per second => 0.5s real time / frame
        fps_clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
