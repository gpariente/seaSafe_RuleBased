# ui_helpers.py
"""
UI Helpers Module

This module contains helper functions for drawing user interface elements,
including the y-axis panel, x-axis panel, and a star shape on the screen.
These functions are intended to be used by the SeaSafe simulator to render
coordinate axes and markers.
"""

import pygame

def draw_y_axis_panel(screen, panel_rect, map_size, font):
    """
    Draws a vertical coordinate panel (y-axis) in the provided rectangle.

    Parameters:
        screen (pygame.Surface): The target surface to draw on.
        panel_rect (pygame.Rect): The rectangle area reserved for the y-axis.
        map_size (float): The maximum value on the y-axis (in nautical miles).
        font (pygame.font.Font): The font used to render the axis labels.
    """
    # Draw the background for the panel.
    pygame.draw.rect(screen, (220, 220, 220), panel_rect)  # Light grey background
    
    # Define the x-position for the axis and vertical margins.
    axis_x = panel_rect.x + 30
    axis_top = panel_rect.y + 10
    axis_bottom = panel_rect.y + panel_rect.height - 10
    
    # Draw the vertical line representing the y-axis.
    pygame.draw.line(screen, (0, 0, 0), (axis_x, axis_top), (axis_x, axis_bottom), 2)
    
    # Set the number of ticks to draw on the y-axis.
    num_ticks = 5
    for i in range(num_ticks):
        # Calculate the fractional position of the tick.
        fraction = i / (num_ticks - 1)
        # Determine the y-position for this tick.
        y_pos = axis_bottom - fraction * (axis_bottom - axis_top)
        # Draw the tick mark.
        pygame.draw.line(screen, (0, 0, 0), (axis_x, y_pos), (axis_x - 10, y_pos), 2)
        # Calculate the label value for the tick.
        value = fraction * map_size
        # Render the label with one decimal precision.
        label = font.render(f"{value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect()
        # Position the label to the left of the tick.
        label_rect.right = axis_x - 12
        label_rect.centery = y_pos
        # Blit the label onto the screen.
        screen.blit(label, label_rect)

def draw_x_axis_panel(screen, panel_rect, map_size, font):
    """
    Draws a horizontal coordinate panel (x-axis) in the provided rectangle.

    Parameters:
        screen (pygame.Surface): The target surface to draw on.
        panel_rect (pygame.Rect): The rectangle area reserved for the x-axis.
        map_size (float): The maximum value on the x-axis (in nautical miles).
        font (pygame.font.Font): The font used to render the axis labels.
    """
    # Draw the background for the panel.
    pygame.draw.rect(screen, (220, 220, 220), panel_rect)
    
    # Define the y-position for the axis and horizontal margins.
    axis_y = panel_rect.y + 20
    axis_left = panel_rect.x + 10
    axis_right = panel_rect.x + panel_rect.width - 10
    
    # Draw the horizontal line representing the x-axis.
    pygame.draw.line(screen, (0, 0, 0), (axis_left, axis_y), (axis_right, axis_y), 2)
    
    # Set the number of ticks to draw on the x-axis.
    num_ticks = 5
    for i in range(num_ticks):
        # Calculate the fractional position of the tick.
        fraction = i / (num_ticks - 1)
        # Determine the x-position for this tick.
        x_pos = axis_left + fraction * (axis_right - axis_left)
        # Draw the tick mark.
        pygame.draw.line(screen, (0, 0, 0), (x_pos, axis_y), (x_pos, axis_y + 10), 2)
        # Calculate the label value for the tick.
        value = fraction * map_size
        # Render the label with one decimal precision.
        label = font.render(f"{value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect()
        # Center the label horizontally at the tick.
        label_rect.centerx = x_pos
        # Position the label just below the tick mark.
        label_rect.top = axis_y + 12
        # Blit the label onto the screen.
        screen.blit(label, label_rect)

def draw_star(screen, center, radius, color):
    """
    Draws a 5-pointed star at the given center with the specified radius and color.

    Parameters:
        screen (pygame.Surface): The target surface to draw on.
        center (tuple): A tuple (x, y) indicating the center of the star.
        radius (float): The radius of the star (distance from center to outer points).
        color (tuple): The color of the star, as an RGB tuple.
    """
    # Import math if not already imported.
    import math
    points = []
    inner_radius = radius * 0.5  # Define inner radius for the star points.
    # The star is drawn as a 10-pointed polygon, alternating between outer and inner points.
    for i in range(10):
        angle = math.radians(i * 36)  # 36° between points.
        r = radius if i % 2 == 0 else inner_radius
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))
    # Draw the star as a filled polygon.
    pygame.draw.polygon(screen, color, points)
