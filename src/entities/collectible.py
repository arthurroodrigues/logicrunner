import math
import os
import pygame

from src import config
from src.core.utils import draw_text


COLLECTIBLES = {
    "coin": {"label": "$", "color": (255, 225, 90), "points": 25},
}

_COIN_IMAGE_CACHE: dict[int, pygame.Surface] = {}
_COIN_SOURCE: pygame.Surface | None = None


def _get_coin_image(size: int) -> pygame.Surface:
    global _COIN_SOURCE
    if _COIN_SOURCE is None:
        path = os.path.join("assets", "moeda.png")
        _COIN_SOURCE = pygame.image.load(path).convert_alpha()
    if size not in _COIN_IMAGE_CACHE:
        _COIN_IMAGE_CACHE[size] = pygame.transform.smoothscale(_COIN_SOURCE, (size, size))
    return _COIN_IMAGE_CACHE[size]


class Collectible:
    def __init__(self, lane: int, kind: str, speed: float, z: float) -> None:
        self.lane = lane
        self.kind = kind
        self.x = config.WORLD_LANE_POSITIONS[lane]
        self.z = z
        self.speed = speed
        self.phase = 0.0
        self.data = COLLECTIBLES[kind]

    @property
    def y(self) -> float:
        return self.z

    def update(self, dt: float, speed_multiplier: float) -> None:
        self.z -= self.speed * speed_multiplier * dt
        self.phase += dt * 8

    def is_offscreen(self) -> bool:
        return self.z < -3

    def collides_with(self, player: object) -> bool:
        return self.z <= config.COLLISION_Z and abs(player.x - self.x) <= config.LANE_WIDTH_WORLD * 0.85

    def draw(self, surface: pygame.Surface, font: pygame.font.Font, projection: object) -> None:
        sx, sy, scale = projection.project(self.x, 0.92 + math.sin(self.phase) * 0.12, self.z)
        radius = max(3, int(0.28 * scale))
        if sy < config.HORIZON_Y - 30 or sy > config.SCREEN_HEIGHT + 30:
            return
        if self.kind == "coin":
            size = radius * 2
            img = _get_coin_image(size)
            surface.blit(img, (sx - radius, sy - radius))
        else:
            color = self.data["color"]
            pygame.draw.circle(surface, color, (sx, sy), radius, 2)
            pygame.draw.circle(surface, (10, 18, 36), (sx, sy), max(1, radius - 4))
            if radius > 12:
                draw_text(surface, self.data["label"], font, config.WHITE, center=(sx, sy), max_width=radius * 2)
