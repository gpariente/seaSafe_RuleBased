# ui_component.py
"""
User Interface Components Module

This module contains custom UI components used in the SeaSafe Simulator.
Currently, it defines a TextBox class that handles user text input,
drawing, and simple value retrieval (as string, float, or int).
"""

import pygame

class TextBox:
    def __init__(self, rect, font, initial_text=""):
        """
        Initializes a new TextBox.

        Parameters:
            rect (tuple or pygame.Rect): The rectangle (x, y, width, height) that defines the textbox area.
            font (pygame.font.Font): The font used to render the text.
            initial_text (str): The initial text to display in the textbox (default is an empty string).
        """
        # Save the original rectangle (as the base for scaling) and create a copy for current use.
        self.base_rect = pygame.Rect(rect)
        self.rect = self.base_rect.copy()
        self.font = font
        self.text = initial_text
        self.active = False  # Indicates whether the textbox is active (i.e., focused)

    def update_rect(self, scale_x, scale_y):
        """
        Updates the textbox's rectangle based on the given scale factors.
        
        This method is used when the application window is resized so that the textbox scales accordingly.
        
        Parameters:
            scale_x (float): The horizontal scaling factor.
            scale_y (float): The vertical scaling factor.
        """
        self.rect = pygame.Rect(
            int(self.base_rect.x * scale_x),
            int(self.base_rect.y * scale_y),
            int(self.base_rect.width * scale_x),
            int(self.base_rect.height * scale_y)
        )

    def handle_event(self, event):
        """
        Processes a single Pygame event for the textbox.
        
        - Activates the textbox if it is clicked.
        - Handles key events for text input, deletion, and ignoring the Return key.
        
        Parameters:
            event (pygame.event.Event): The event to process.
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Activate the textbox if the mouse click occurs inside its rectangle.
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                # Remove the last character on Backspace.
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                # Do nothing on Return (could be extended in the future).
                pass
            else:
                # Append the typed character to the textbox's text.
                self.text += event.unicode

    def draw(self, screen):
        """
        Renders the textbox on the given screen.
        
        Draws a colored border (green if active, grey if inactive) and the current text.
        
        Parameters:
            screen (pygame.Surface): The surface on which to draw the textbox.
        """
        # Choose border color based on whether the textbox is active.
        color = (40, 200, 40) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)
        # Render the text with white color.
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        # Draw the text slightly inset within the rectangle.
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))

    def get_str(self):
        """
        Returns the current text of the textbox with surrounding whitespace removed.
        
        Returns:
            str: The trimmed text.
        """
        return self.text.strip()

    def get_float(self, default=0.0):
        """
        Attempts to convert the textbox text to a float.
        
        Parameters:
            default (float): The value to return if conversion fails (default is 0.0).
        
        Returns:
            float: The converted value or the default if conversion fails.
        """
        try:
            return float(self.text)
        except ValueError:
            return default

    def get_int(self, default=0):
        """
        Attempts to convert the textbox text to an integer.
        
        Parameters:
            default (int): The value to return if conversion fails (default is 0).
        
        Returns:
            int: The converted value or the default if conversion fails.
        """
        try:
            return int(self.text)
        except ValueError:
            return default
