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
