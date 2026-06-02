import pygame

from src import config


class Button:
    def __init__(self, rect: pygame.Rect, text: str) -> None:
        self.rect = rect
        self.text = text

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, selected: bool = False, disabled: bool = False) -> None:
        border = config.MUTED if disabled else config.CYAN if selected else config.PURPLE
        text_color = config.MUTED if disabled else config.WHITE
        pygame.draw.rect(surface, config.PANEL, self.rect, border_radius=8)
        pygame.draw.rect(surface, border, self.rect, 2, border_radius=8)
        label = font.render(self.text, True, text_color)
        surface.blit(label, label.get_rect(center=self.rect.center))
