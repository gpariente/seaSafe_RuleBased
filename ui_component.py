# ui_component.py
import pygame

class TextBox:
    def __init__(self, rect, font, initial_text=""):
        self.base_rect = pygame.Rect(rect)
        self.rect = self.base_rect.copy()
        self.font = font
        self.text = initial_text
        self.active = False

    def update_rect(self, scale_x, scale_y):
        self.rect = pygame.Rect(
            int(self.base_rect.x * scale_x),
            int(self.base_rect.y * scale_y),
            int(self.base_rect.width * scale_x),
            int(self.base_rect.height * scale_y)
        )

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
        color = (40, 200, 40) if self.active else (200, 200, 200)
        pygame.draw.rect(screen, color, self.rect, 2)
        txt_surf = self.font.render(self.text, True, (255, 255, 255))
        screen.blit(txt_surf, (self.rect.x + 5, self.rect.y + 5))

    def get_str(self):
        return self.text.strip()

    def get_float(self, default=0.0):
        try:
            return float(self.text)
        except ValueError:
            return default

    def get_int(self, default=0):
        try:
            return int(self.text)
        except ValueError:
            return default
