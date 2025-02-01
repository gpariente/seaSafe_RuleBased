# main.py
import pygame
import sys
from states.main_menu import MainMenuState
from states.simulation_ui import SimulationState  # Needed to check state type

def main():
    pygame.init()
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("SeaSafe Simulator")
    clock = pygame.time.Clock()

    # Start with the main menu state.
    current_state = MainMenuState(screen)

    running = True
    while running:
        # Use a slower tick (3 FPS) if in SimulationState; else 30 FPS.
        if current_state.__class__.__name__ == "SimulationState":
            dt = clock.tick(3) / 1000.0
        else:
            dt = clock.tick(30) / 1000.0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        # Process events first, then update, then render.
        current_state.handle_events(events)
        current_state.update(dt)
        current_state.render(screen)
        pygame.display.flip()

        next_state = current_state.get_next_state()
        if next_state is not None:
            current_state = next_state

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
