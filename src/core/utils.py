import math
import os
from collections import deque
from typing import Iterable

import pygame

# ── Sprite loading with automatic white-background removal ───────────────────

_SPRITE_SOURCES: dict[str, pygame.Surface] = {}
_SPRITE_SCALED:  dict[tuple[str, int, int], pygame.Surface] = {}


def _flood_remove_bg(surf: pygame.Surface, threshold: int = 235) -> pygame.Surface:
    """Return a copy of surf with the exterior white/near-white background erased."""
    out = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    out.blit(surf, (0, 0))
    w, h = out.get_size()
    visited = bytearray(w * h)
    queue: deque = deque()

    def _seed(x: int, y: int) -> None:
        idx = y * w + x
        if not visited[idx]:
            r, g, b, _ = out.get_at((x, y))
            if r >= threshold and g >= threshold and b >= threshold:
                visited[idx] = 1
                queue.append((x, y))

    for x in range(w):
        _seed(x, 0); _seed(x, h - 1)
    for y in range(1, h - 1):
        _seed(0, y); _seed(w - 1, y)

    while queue:
        x, y = queue.popleft()
        out.set_at((x, y), (0, 0, 0, 0))
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h:
                idx = ny * w + nx
                if not visited[idx]:
                    r, g, b, _ = out.get_at((nx, ny))
                    if r >= threshold and g >= threshold and b >= threshold:
                        visited[idx] = 1
                        queue.append((nx, ny))
    return out


def load_sprite(filename: str, work_size: int = 256) -> pygame.Surface:
    """Load an asset image, remove white background, and cache at work_size."""
    if filename in _SPRITE_SOURCES:
        return _SPRITE_SOURCES[filename]
    path = os.path.join("assets", filename)
    raw = pygame.image.load(path).convert_alpha()
    small = pygame.transform.smoothscale(raw, (work_size, work_size))
    cleaned = _flood_remove_bg(small)
    _SPRITE_SOURCES[filename] = cleaned
    return cleaned


def get_sprite_scaled(filename: str, width: int, height: int) -> pygame.Surface:
    """Return a cached scaled version of the sprite."""
    key = (filename, width, height)
    if key not in _SPRITE_SCALED:
        src = load_sprite(filename)
        _SPRITE_SCALED[key] = pygame.transform.smoothscale(src, (width, height))
    return _SPRITE_SCALED[key]


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
