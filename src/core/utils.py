import math
from typing import Iterable

import pygame


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    center: tuple[int, int] | None = None,
    topleft: tuple[int, int] | None = None,
    max_width: int | None = None,
) -> pygame.Rect:
    if max_width is None or font.size(text)[0] <= max_width:
        rendered = font.render(text, True, color)
        rect = rendered.get_rect()
        if center:
            rect.center = center
        if topleft:
            rect.topleft = topleft
        surface.blit(rendered, rect)
        return rect

    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if font.size(candidate)[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)

    line_height = font.get_linesize()
    width = max(font.size(line)[0] for line in lines)
    height = line_height * len(lines)
    rect = pygame.Rect(0, 0, width, height)
    if center:
        rect.center = center
    if topleft:
        rect.topleft = topleft
    for index, line in enumerate(lines):
        rendered = font.render(line, True, color)
        surface.blit(rendered, (rect.x, rect.y + index * line_height))
    return rect


def pulse(alpha_min: int, alpha_max: int, speed: float, ticks: int) -> int:
    wave = (math.sin(ticks * speed) + 1) / 2
    return int(alpha_min + (alpha_max - alpha_min) * wave)


def first_existing(items: Iterable[str], default: str) -> str:
    for item in items:
        if item:
            return item
    return default
