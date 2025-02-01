# draw_utils.py
import pygame
import math

def draw_button(screen, rect, text, font, color=(0, 0, 200)):
    pygame.draw.rect(screen, color, rect, border_radius=5)
    label = font.render(text, True, (255, 255, 255))
    lx = rect.x + (rect.width - label.get_width()) // 2
    ly = rect.y + (rect.height - label.get_height()) // 2
    screen.blit(label, (lx, ly))

def draw_scrolling_bg(screen, bg_img, scroll_x, scroll_speed, dt):
    w = bg_img.get_width()
    scroll_x = (scroll_x + scroll_speed * dt) % w
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
    rotated = pygame.transform.rotate(ship_surf, ship.heading)
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
        pygame.draw.line(screen, (0,0,0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0,0,0))
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
        pygame.draw.line(screen, (0,0,0), tick_start, tick_end, 2)
        label = font.render(f"{tick_value:.1f}", True, (0,0,0))
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
    pygame.draw.rect(screen, (200,200,200), minimap_rect)
    pygame.draw.rect(screen, (0,0,0), minimap_rect, 2)
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
        pygame.draw.line(screen, (100,100,100), (x, pos[1]), (x, pos[1]+size), 1)
        y = pos[1] + size - i * scale
        pygame.draw.line(screen, (100,100,100), (pos[0], y), (pos[0]+size, y), 1)

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
