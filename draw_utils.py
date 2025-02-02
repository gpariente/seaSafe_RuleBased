# draw_utils.py
"""
Drawing Utilities Module

This module contains helper functions to draw various UI elements for the SeaSafe Simulator.
These include functions to draw buttons, scrolling backgrounds, ship trails, ship rectangles,
safety circles, coordinate axis labels, grids, stars, minimaps, and dashed lines.
"""

import pygame
import math

def draw_button(screen, rect, text, font, color=(0, 0, 200)):
    """
    Draws a rectangular button with centered text.

    Parameters:
        screen (pygame.Surface): The surface on which to draw the button.
        rect (pygame.Rect): The rectangle defining the button's area.
        text (str): The text to display on the button.
        font (pygame.font.Font): The font used to render the text.
        color (tuple): The RGB color of the button (default is (0, 0, 200)).
    """
    pygame.draw.rect(screen, color, rect, border_radius=5)
    label = font.render(text, True, (255, 255, 255))
    lx = rect.x + (rect.width - label.get_width()) // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    screen.blit(label, (lx, ly))

def draw_scrolling_bg(screen, bg_img, scroll_x, scroll_speed, dt):
    """
    Draws a horizontally scrolling background image.

    Parameters:
        screen (pygame.Surface): The target surface.
        bg_img (pygame.Surface): The background image.
        scroll_x (float): The current horizontal scroll offset.
        scroll_speed (float): The scrolling speed in pixels per second.
        dt (float): The time elapsed since the last update (in seconds).

    Returns:
        float: The updated scroll offset.
    """
    w = bg_img.get_width()
    # Update the scroll offset using dt and scroll_speed, and wrap around using modulus.
    scroll_x = (scroll_x + scroll_speed * dt) % w
    screen.blit(bg_img, (-scroll_x, 0))
    screen.blit(bg_img, (-scroll_x + w, 0))
    return scroll_x

def draw_ship_trail(screen, ship, nm_to_px, map_height, offset_x=0, offset_y=0):
    """
    Draws the trail of a ship as a series of connected line segments.

    Parameters:
        screen (pygame.Surface): The surface to draw on.
        ship (Ship): The ship whose trail is to be drawn. The ship must have a 'trail' attribute
                     (list of (x,y) tuples).
        nm_to_px (float): Conversion factor from Nautical Miles (NM) to pixels.
        map_height (int): The height of the map in pixels.
        offset_x (int): Horizontal offset for drawing.
        offset_y (int): Vertical offset for drawing.
    """
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
    """
    Draws a ship as a rotated rectangle representing its physical dimensions.

    Parameters:
        screen (pygame.Surface): The target surface.
        ship (Ship): The ship object with attributes 'x', 'y', 'heading', 'length_m', 'width_m', and 'color'.
        nm_to_px (float): Conversion factor from Nautical Miles (NM) to pixels.
        map_height (int): Height of the map in pixels.
        offset_x (int): Horizontal offset for drawing.
        offset_y (int): Vertical offset for drawing.
    """
    # Convert ship dimensions from meters to Nautical Miles (1 NM ≈ 1852 m)
    length_nm = ship.length_m / 1852.0
    width_nm  = ship.width_m  / 1852.0
    length_px = length_nm * nm_to_px
    width_px  = width_nm * nm_to_px
    x_screen = offset_x + ship.x * nm_to_px
    y_screen = offset_y + map_height - (ship.y * nm_to_px)
    # Ensure at least 1 pixel width/length.
    surf_l = max(1, int(length_px))
    surf_w = max(1, int(width_px))
    ship_surf = pygame.Surface((surf_l, surf_w), pygame.SRCALPHA)
    ship_surf.fill(ship.color)
    # Rotate the ship's surface based on its heading.
    rotated = pygame.transform.rotate(ship_surf, ship.heading)
    rect = rotated.get_rect()
    rect.center = (x_screen, y_screen)
    screen.blit(rotated, rect)

def draw_safety_circle(screen, ship, safe_distance_nm, nm_to_px, map_height, offset_x=0, offset_y=0):
    """
    Draws a safety circle around the ship, indicating the safety distance (in NM).

    Parameters:
        screen (pygame.Surface): The target surface.
        ship (Ship): The ship object with attributes 'x', 'y', and 'color'.
        safe_distance_nm (float): The safety distance in Nautical Miles.
        nm_to_px (float): Conversion factor from NM to pixels.
        map_height (int): Height of the map in pixels.
        offset_x (int): Horizontal offset.
        offset_y (int): Vertical offset.
    """
    radius_px = int(safe_distance_nm * nm_to_px)
    center_x = int(offset_x + ship.x * nm_to_px)
    center_y = int(offset_y + map_height - (ship.y * nm_to_px))
    if radius_px > 0:
        pygame.draw.circle(screen, (255, 0, 0), (center_x, center_y), radius_px, 1)

def draw_y_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    """
    Draws vertical axis labels inside a given margin rectangle.

    Parameters:
        screen (pygame.Surface): The target surface.
        margin_rect (pygame.Rect): The rectangle area where the labels will be drawn.
        map_size (float): The maximum value of the axis (e.g., map size in NM).
        font (pygame.font.Font): The font used for rendering labels.
        tick_step (float): The value interval between ticks (default 0.5).
    """
    bg_color = (130, 180, 255)
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Calculate the y-position for the tick relative to the margin.
        y = margin_rect.bottom - (tick_value / map_size) * margin_rect.height
        tick_start = (margin_rect.right - 10, y)
        tick_end = (margin_rect.right, y)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midright=(margin_rect.right - 12, y))
        screen.blit(label, label_rect)

def draw_x_axis_labels_in_margin(screen, margin_rect, map_size, font, tick_step=0.5):
    """
    Draws horizontal axis labels inside a given margin rectangle.

    Parameters:
        screen (pygame.Surface): The target surface.
        margin_rect (pygame.Rect): The rectangle area where the labels will be drawn.
        map_size (float): The maximum value of the axis (e.g., map size in NM).
        font (pygame.font.Font): The font used for rendering labels.
        tick_step (float): The value interval between ticks (default 0.5).
    """
    bg_color = (130, 180, 255)
    pygame.draw.rect(screen, bg_color, margin_rect)
    num_ticks = int(map_size / tick_step) + 1
    for i in range(num_ticks):
        tick_value = i * tick_step
        # Calculate the x-position for the tick relative to the margin.
        x = margin_rect.left + (tick_value / map_size) * margin_rect.width
        tick_start = (x, margin_rect.top)
        tick_end = (x, margin_rect.top + 10)
        pygame.draw.line(screen, (0, 0, 0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0, 0, 0))
        label_rect = label.get_rect(midtop=(x, margin_rect.top + 12))
        screen.blit(label, label_rect)

def draw_grid(screen, map_rect, map_size, nm_to_px, tick_step=0.5, color=(200, 200, 200)):
    """
    Draws a grid over a map area.

    Parameters:
        screen (pygame.Surface): The target surface.
        map_rect (pygame.Rect): The rectangle defining the map area.
        map_size (float): The size of the map in Nautical Miles.
        nm_to_px (float): Conversion factor from NM to pixels.
        tick_step (float): The interval (in NM) between grid lines.
        color (tuple): The color of the grid lines.
    """
    num_ticks = int(map_size / tick_step) + 1
    # Draw vertical grid lines.
    for i in range(num_ticks):
        x = map_rect.left + i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (x, map_rect.top), (x, map_rect.bottom), 1)
    # Draw horizontal grid lines.
    for i in range(num_ticks):
        y = map_rect.bottom - i * tick_step * nm_to_px
        pygame.draw.line(screen, color, (map_rect.left, y), (map_rect.right, y), 1)

def draw_star(screen, center, radius, color):
    """
    Draws a 5-pointed star at the given center.

    Parameters:
        screen (pygame.Surface): The target surface.
        center (tuple): A tuple (x, y) representing the center of the star.
        radius (float): The radius of the star (distance from center to outer points).
        color (tuple): The RGB color of the star.
    """
    points = []
    inner_radius = radius * 0.5  # Define inner radius for alternating points.
    for i in range(10):
        angle = math.radians(i * 36)  # 36° between each point.
        r = radius if i % 2 == 0 else inner_radius
        x = center[0] + r * math.cos(angle)
        y = center[1] + r * math.sin(angle)
        points.append((x, y))
    pygame.draw.polygon(screen, color, points)

def draw_minimap(screen, ships, map_size, pos, size):
    """
    Draws a minimap that shows the positions of ships and their destinations.

    Parameters:
        screen (pygame.Surface): The target surface.
        ships (list): A list of ship objects (each with x, y, dest_x, dest_y, and color attributes).
        map_size (float): The size of the map in Nautical Miles.
        pos (tuple): The (x, y) position for the top-left corner of the minimap.
        size (int): The width and height (in pixels) of the square minimap.
    """
    minimap_rect = pygame.Rect(pos[0], pos[1], size, size)
    pygame.draw.rect(screen, (200, 200, 200), minimap_rect)
    pygame.draw.rect(screen, (0, 0, 0), minimap_rect, 2)
    scale = size / map_size
    # Draw source markers and destination stars for each ship.
    for s in ships:
        src_x = pos[0] + s.x * scale
        src_y = pos[1] + size - s.y * scale
        pygame.draw.circle(screen, s.color, (int(src_x), int(src_y)), 3)
        dest_x = pos[0] + s.dest_x * scale
        dest_y = pos[1] + size - s.dest_y * scale
        draw_star(screen, (int(dest_x), int(dest_y)), 5, s.color)
    # Draw grid lines on the minimap.
    for i in range(int(map_size)+1):
        x = pos[0] + i * scale
        pygame.draw.line(screen, (100, 100, 100), (x, pos[1]), (x, pos[1]+size), 1)
        y = pos[1] + size - i * scale
        pygame.draw.line(screen, (100, 100, 100), (pos[0], y), (pos[0]+size, y), 1)

def draw_dashed_line(screen, color, start_pos, end_pos, dash_length=5, space_length=3):
    """
    Draws a dashed line between two points.

    Parameters:
        screen (pygame.Surface): The target surface.
        color (tuple): The RGB color of the dashed line.
        start_pos (tuple): The starting (x, y) coordinate.
        end_pos (tuple): The ending (x, y) coordinate.
        dash_length (int): The length of each dash in pixels.
        space_length (int): The length of the space between dashes in pixels.
    """
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
