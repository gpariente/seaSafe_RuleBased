# main.py
"""
SeaSafe Simulator Main Entry Point

This module initializes the Pygame environment, sets up the main window,
and manages the main loop that handles event processing, state updates,
and rendering of the different screens (states) of the simulator.

States are managed by transitioning from one state to the next based on
user interaction (e.g., moving from the main menu to the simulation screen).

Author: [Your Name]
Date: [Date]
"""

import pygame
import sys
from states.main_menu import MainMenuState
from states.simulation_ui import SimulationState  # Used to check state type for FPS settings

def main():
    # Initialize the Pygame library.
    pygame.init()
    
    # Create a resizable window with an initial resolution of 800x600.
    screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE)
    pygame.display.set_caption("SeaSafe Simulator")
    
    # Create a clock object to manage frame rate.
    clock = pygame.time.Clock()

    # Initialize the current state as the Main Menu.
    current_state = MainMenuState(screen)

    running = True
    while running:
        # Use a slower tick (3 FPS) if the current state is SimulationState;
        # otherwise, use 30 FPS for smoother UI experience.
        if current_state.__class__.__name__ == "SimulationState":
            dt = clock.tick(3) / 1000.0  # dt in seconds
        else:
            dt = clock.tick(30) / 1000.0
        
        # Retrieve all Pygame events.
        events = pygame.event.get()
        for event in events:
            # If the user closes the window, exit the loop.
            if event.type == pygame.QUIT:
                running = False
            # Handle window resize events.
            elif event.type == pygame.VIDEORESIZE:
                screen = pygame.display.set_mode((event.w, event.h), pygame.RESIZABLE)
        
        # Delegate event handling, state updates, and rendering to the current state.
        current_state.handle_events(events)
        current_state.update(dt)
        current_state.render(screen)
        pygame.display.flip()  # Update the full display surface to the screen.

        # Check if the current state requests a transition to another state.
        next_state = current_state.get_next_state()
        if next_state is not None:
            current_state = next_state

    # Quit Pygame and exit the program.
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
